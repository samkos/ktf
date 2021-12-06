#!/usr/bin/python3
# GraphQL helpers methods to submit a new oil spill via a graphQL API hosted on AWS
# WRITTEN BY SAMUEL KORTAS, KAUST SUPERCOMPUTING LABORATORY
# COPYRIGHTED, 2021


from base64 import b64encode, decode
import boto3
from datetime import datetime
import json 
import os
import simplejson
import sys
import traceback
import threading
import time
from uuid import uuid4
from urllib import request
import websocket
from .engine import *
from .env import *


##########################################################################################################
# Global parameters
##########################################################################################################


# Set up Timeout Globals
timeout_timer = None
timeout_interval = 10


##########################################################################################################
# helpers functions
##########################################################################################################


def getCurrentTime():
    return time.strftime('%Y%m%d:%H%M%S')

def getCurrentDate():
    return time.strftime('%Y%m%d')

# Calculate UTC time in ISO format (AWS Friendly): YYYY-MM-DDTHH:mm:ssZ
def header_time():
    return datetime.utcnow().isoformat(sep='T',timespec='seconds') + 'Z'

# Encode Using Base 64
def header_encode( header_obj ):
    return b64encode(simplejson.dumps(header_obj).encode('utf-8')).decode('utf-8')



##########################################################################################################
# Connection and Authentication parameters
##########################################################################################################


settings = json.load(open('../lib/AWS_credentials.json'))

# Constants Copied from AppSync API 'Settings'
API_URL = settings["API_URL"]
API_KEY = settings["API_KEY"]

# Used by the subscription
WSS_URL = API_URL.replace('https','wss').replace('appsync-api','appsync-realtime-api')
HOST = API_URL.replace('https://','').replace('/graphql','')

# Subscription ID (client generated)
SUB_ID = str(uuid4())

# API key authentication header
api_header = {
    'host':HOST,
    'x-api-key':API_KEY
}

# Set up the connection URL, which includes the Authentication Header
#   and a payload of '{}'.  All info is base 64 encoded
connection_url = WSS_URL + '?header=' + header_encode(api_header) + '&payload=e30='

##########################################################################################################
# GRAPHQL queries, mutations and subscription
##########################################################################################################

CREATE_EXPERIMENT = """
mutation createExperiment($input: CreateExperimentInput!) {
  createExperiment(input: $input) {
    target
    user
    name
    date
    results
    id
    createdAt
    updatedAt
  }
}
"""

UPDATE_EXPERIMENT = """
mutation updateExperiment($input: UpdateExperimentInput!) {
  updateExperiment(input: $input) {
    target
    user
    name
    date
    results
    id
    createdAt
    updatedAt
  }
}
"""

GET_EXPERIMENT = """
    query getF($id: ID!) {
    getExperiment(id: $id) {
      target
      user
      name
      date
      results
      id
    }
  }
"""

DELETE_EXPERIMENT = """
mutation deleteExperiment($input: DeleteExperimentInput!) {
  deleteExperiment(input: $input) {
    target
    user
    name
    date
    results
    id
    createdAt
    updatedAt
  }
}
"""

# GraphQL subscription Registration object
GQL_SUBSCRIPTION_2 = json.dumps({
    'query': """subscription onUpdateExperiment { 
    onCreateExperiment {
      target
      user
      name
      date
      results
      id
    }
    }""",
    'variables': {}
})


##########################################################################################################
# GRAPHQL client
##########################################################################################################

class GraphqlClient():

    def __init__(self, log_debug, args):
        self.endpoint = API_URL
        self.headers = {'x-api-key': API_KEY}
        self.log_debug = log_debug
        self.ags = args


    @staticmethod
    def serialization_helper(o):
        if isinstance(o, datetime):
            return o.strftime('%Y-%m-%dT%H:%M:%S.000Z')

    def execute(self, query, operation_name, variables={}):
        data = simplejson.dumps({
            "query": query,
            "variables": variables,
            "operationName": operation_name
        },
            default=self.serialization_helper,
            ignore_nan=True
        )
        r = request.Request(
            headers=self.headers,
            url=self.endpoint,
            method='POST',
            data=data.encode('utf8')
        )
        response = request.urlopen(r).read()


        return self.format_response(response, query, operation_name)

    def format_response(self,response, query, operation_name):
        self.log_debug(pprint.pformat(response), level=0, trace="GQL")
        res = response.decode('utf8')
        response_array = simplejson.loads(res)
        self.log_debug(pprint.pformat(response_array), level=0, trace="GQL")
        response_data = response_array
        keys = response_array.keys()
        if "errors" in keys:
            error_message = "Unknown error occured in gql query or mutation"
            print("*** GQL ERROR *** operation_name:", operation_name)
            print("*** GQL ERROR *** query:", query)
            for l in response_array["errors"]:
                for k,v in l.items():
                    print("*** GQL ERROR ***",k,v)
                    if k=="message":
                        error_message = v
            raise Exception('GQL Error in %s' % operation_name, error_message)
        else:
            keys = response_array["data"].keys()
            if not(len(keys)==1):
                error_message = "answer received but don't know which part to take as an answer"
                print("*** GQL ERROR *** operation_name:", operation_name)
                print("*** GQL ERROR *** query:", query)
                print("*** GQL ERROR *** response:", response_array)
                raise Exception('GQL Error in GraphqlClient.format_response of %s' % operation_name, error_message)
            main_key = ""
            for k in keys:
                main_key  = k
            self.log_debug(pprint.pformat(keys, main_key, len(keys)), level=0, trace="GQL")
            return response_array["data"][main_key]



    ##########################################################################################################
    # subscribing methods
    ##########################################################################################################

    # reset the keep alive timeout daemon thread
    def reset_timer(self, ws ):
        global timeout_timer
        global timeout_interval

        if (timeout_timer):
            timeout_timer.cancel()
        timeout_timer = threading.Timer( timeout_interval, lambda: ws.close() )
        timeout_timer.daemon = True
        timeout_timer.start()


    # Socket Event Callbacks, used in WebSocketApp Constructor
    def on_message(self, ws, message):
        global timeout_timer
        global timeout_interval

        self.log_debug('### message ###', level=0, trace="GQL")
        self.log_debug('<< message received >>', level=0, trace="GQL")
        self.log_debug(message, level=0, trace="GQL")
        self.log_debug('<<----------------->>', level=0, trace="GQL")

        message_object = json.loads(message)
        message_type   = message_object['type']

        if( message_type == 'ka' ):
            reset_timer(ws)

        elif( message_type == 'connection_ack' ):
            print('<<-- ack -->>')
            timeout_interval = int(json.dumps(message_object['payload']['connectionTimeoutMs']))

            register = {
                'id': SUB_ID,
                'payload': {
                    'data': GQL_SUBSCRIPTION_2,
                    'extensions': {
                        'authorization': {
                            'host':HOST,
                            'x-api-key':API_KEY
                    }
                    }
                },
                'type': 'start'
            }
            start_sub = json.dumps(register)
            self.log_debug('>> '+ start_sub , level=0, trace="GQL")
            ws.send(start_sub)

        elif(message_type == 'data'):
            run  = message_object["payload"]["data"]["onCreateExperiment"]
            if DEBUG or True:
                print('### message ###')
                print('<< message received >>')
                print(message)
                print('<<<<<<<<<<<or>>>>>>>>')
                print(run)
                print('<<----------------->>')

            try:
                self.runExperiment(run)
            except:
                print("problem with run")
                traceback.print_exc()

        elif(message_object['type'] == 'error'):
            print ('Error from AppSync: ' + message_object['payload'])
        
    def on_error(self, ws, error):
        print('### error ###')
        print(error)

    def on_close(self, ws):
        print('### closed ###')

    def on_open(self, ws):
        print('### runner connected ###')
        init = {
            'type': 'connection_init'
        }
        init_conn = json.dumps(init)
        self.log_debug('>> '+ init_conn, level=0, trace="GQL")
        ws.send(init_conn)

    def subscribe_and_wait_forever(self, runOilSpill):

        # Create the websocket connection to AppSync's real-time endpoint
        #  also defines callback functions for websocket events
        #  NOTE: The connection requires a subprotocol 'graphql-ws'
        self.log_debug( 'Subscribing while connecting to: ' + connection_url , level=0, trace="GQL")

        self.runOilSpill = runOilSpill
            
        ws = websocket.WebSocketApp( connection_url,
                                     subprotocols=['graphql-ws'],
                                     on_open    = self.on_open,
                                     on_message = self.on_message,
                                     on_error   = self.on_error,
                                     on_close   = self.on_close,)

        ws.run_forever()



    ##########################################################################################################
    # Experiment operations
    ##########################################################################################################

    def createExperiment(self,input):
        # input["status_timestamp"] = getCurrentTime()
        self.log_debug(pprint.pformat('creating with ' + pprint.pformat(input)), level=0, trace="GQL")
        result = self.execute(query=CREATE_EXPERIMENT, operation_name='createExperiment',
                                  variables={
                                      "input": input
                                  }
                                  )
        return result

    def updateExperiment(self,input):
        # input["status_timestamp"] = getCurrentTime()
        self.log_debug(pprint.pformat('updating with ' + pprint.pformat(input)), level=0, trace="GQL")
        result = self.execute(query=UPDATE_EXPERIMENT, operation_name='updateExperiment',
                                  variables={
                                      "input": input
                                  }
                                  )
        return result

    def getExperiment(self,Experiment_id):
        self.log_debug(pprint.pformat('get Experiment  with ' + pprint.pformat(input)), level=0, trace="GQL")
        result = self.execute(query=GET_EXPERIMENT,  operation_name='getF',
                                  variables={
                                      "id": Experiment_id
                                  }
                                  )
        return result


    def deleteExperiment(self,Experiment_id):
        input = {"id": Experiment_id}
        self.log_debug(pprint.pformat('deleting Experiment  with '  + pprint.pformat(input)), level=0, trace="GQL")
        result = self.execute(query=DELETE_EXPERIMENT,
                                  operation_name='deleteExperiment',
                                  variables={
                                      "input": input
                                  }
                                  )
        return result




        
# gq_client = GraphqlClient(
#     endpoint=API_URL,
#     headers={'x-api-key': API_KEY}
# )
