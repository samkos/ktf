
from pprint import pprint
import boto3
import json


settings = json.load(open("ktf/scripts/AWS_credentials.json"))
print(settings)
def put_movie(exp, title, year, plot,  dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1', aws_access_key_id=settings.aws_access_key_id, aws_secret_access_key=settings.aws_secret_access_key)

    table = dynamodb.Table('ktf-dev')
    response = table.put_item(
       Item={
            'exp': exp,
            'title': title,
            "doc"   : "my doc"
        }
    )
    return response


if __name__ == '__main__':
    movie_resp = put_movie("exp", "xxx", "xxx", "xxx")
    print("Put movie succeeded:")
    # pprint(movie_resp, sort_dicts=False)
