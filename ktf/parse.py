  #########################################################################
  # parse an additional tags from the yalla parameter file
  #########################################################################
  def additional_tag(self, line):
    # direct sweeping of parameter
    matchObj = re.match(r'^#DECIM\s*COMBINE\s*(\S+|_)\s*=\s*(.*)\s*$', line)
    if (matchObj):
      (t, v) = (matchObj.group(1), matchObj.group(2))
      self.log_debug("combine tag definitition: /%s/ " % line, 4, trace='YALLA,PARAMETRIC_DETAIL,PD')
      self.combined_tag[t] = v
      self.direct_tag[t] = v
      self.direct_tag_ordered = self.direct_tag_ordered + [t]
      return True
    # direct setting of parameter
    matchObj = re.match(r'^#DECIM\s*(\S+|_)\s*=\s*(.*)\s*$', line)
    if (matchObj):
      (t, v) = (matchObj.group(1), matchObj.group(2))
      self.log_debug("direct tag definitition: /%s/ " % line, 4, trace='YALLA,PARAMETRIC_DETAIL,PD')
      self.direct_tag[t] = v
      self.direct_tag_ordered = self.direct_tag_ordered + [t]
      return True
    return False

 #########################################################################
  # compute a cartesian product of two dataframe
  #########################################################################
  def cartesian(self, df1, df2):
    rows = itertools.product(df1.iterrows(), df2.iterrows())

    df = pd.DataFrame(left.append(right) for (_, left), (_, right) in rows)
    return df.reset_index(drop=True)

  #########################################################################
  # evaluate a tag from a formula
  #########################################################################
  def eval_tag(self, tag, formula, already_set_variables):
    expr = already_set_variables +\
           "\n%s = %s" % (tag, formula) 
           #"\nrange_orig = range\ndef range_list(*arg):\n    return list(range_orig(*arg))\nrange = range_list" +\
           #"\nrange=range_orig\n"
    try:
      exec(expr)
    except Exception:
      print ('pb',expr)
      self.error('error in evalution of the parameters: expression to be evaluted : %s=%s ' % (tag, formula), \
                 exception=True, exit=True, where="eval_tag")
    value = locals()[tag]
    self.log_debug('expression to be evaluted : %s  -> value of %s = %s' % (expr, tag, value), \
                   4, trace='PARAMETRIC_DETAIL,PD')
    return value

  #########################################################################
  # evaluate tags from a formula
  #########################################################################
  def eval_tags(self, formula, already_set_variables):
    eval_expr = already_set_variables + \
                "\n%s" % (formula)
                # "\nrange_orig = range\ndef range_list(*arg):\n    return list(range_orig(*arg))\nrange = range_list" +\
                # "\nrange=range_orig\n"
    self.log_debug('expression to be evaluated : %s  ' % (eval_expr), \
                   4, trace='PARAMETRIC_PROG_DETAIL')
    try:
      exec(eval_expr)
    except Exception:
      print (eval_expr)
      self.error('error in evaluation of the parameters (eval_tags): expression to be evaluted : %s ' % \
                 (eval_expr), where="eval_tags", exception=True, exit=True)
    values = {}
    variables = locals()
    del variables['formula']
    del variables['already_set_variables']
    del variables['eval_expr']
    del variables['values']

    for tag, value in variables.items():
      if tag.find('__') == -1 and ("%s" % value).find('<') == -1:
        values[tag] = value
        self.log_debug('value of %s = %s' % (tag, value), \
                       4, trace='PARAMETRIC_DETAIL,PD,PARAMETRIC_PROG')
    return values

  #########################################################################
  # apply parameters to template files
  #########################################################################
  def process_templates(self, from_dir='.'):

    pattern = "*.template"
    matches = []
    params = self.parameters.iloc[self.TASK_ID]
    for root, dirnames, filenames in os.walk(from_dir):
        for filename in fnmatch.filter(filenames, pattern):
            f = os.path.join(root, filename)
            matches.append(f)
            self.log_debug('processing template file %s' % f,4,trace='TEMPLATE')
            content = "".join(open(f).readlines())
            for k in self.parameters.columns:
                v = params[k]
                content = content.replace('__%s__' % k, "%s" % v)
            processed_file = open(f.replace('.template', ""), 'w')
            processed_file.write(content)
            processed_file.close()

    return matches
          
 

  #########################################################################
  # read the yalla parameter file in order to submit a pool of jobs
  #########################################################################

  def read_parameter_file(self):
    self.log_debug('reading yalla parameter files %s' % self.args.parameter_file, \
                   2, trace='YALLA,PARAMETRIC_DETAIL,PD')

    if not(os.path.exists(self.args.parameter_file)):
      self.error('Parameter file %s does not exist!!!' % self.args.parameter_file)
    else:
      tags_ok = False
      lines = open(self.args.parameter_file).readlines()+["\n"]

    # warning message is sent to the user if filter is applied on the combination to consider

    if not(self.args.parameter_filter == None) or \
       not(self.args.parameter_range == None):
      if self.args.parameter_filter:
        self.log_info("the filter %s will be applied... Only following lines will be taken into account : " % \
                      (self.args.parameter_filter))
      if self.args.parameter_range:
        self.log_info("only lines %s will be taken " % self.args.parameter_range)

      self.direct_tag = {}
      self.combined_tag = {}
      self.direct_tag_ordered = []
      nb_case = 1

      for line in lines:
        line = clean_line(line)
        if self.additional_tag(line):
          continue
        if len(line) > 0 and not (line[0] == '#'):
          if not(tags_ok):
            tags_ok = True
            continue
          for k in self.direct_tag.keys():
            line = line + " " + self.direct_tag[k]
          self.log_debug('direct_tag: /%s/' % line, 4, trace='PARAMETRIC_DETAIL,PD')
          matchObj = re.match("^.*" + self.args.parameter_filter + ".*$", line)
          # prints all the tests that will be selected
          if (matchObj) and not(self.args.yes):
            if nb_case == 1:
              for k in self.direct_tag.keys():
                print("%6s" % k,end='')
              print

            if not(self.args.parameter_range) or self.args.parameter_range == nb_case:
              print("%3d: " % (nb_case),end="")
              for k in line.split(" "):
                print("%6s " % k[:20],end='')
              print
            nb_case = nb_case + 1

      # askine to the user if he is ok or not
      if not(self.args.spawned):
        self.ask("Is this correct?", default='n')

      tags_ok = False
          
    # direct_tag contains the tags set through #DECIM tag = value
    # it needs to be evaluated on the fly to apply right tag value at a given job
    self.direct_tag = {}
    self.combined_tag = {}
    self.direct_tag_ordered = []
    self.python_tag = {}
    self.python_tag_ordered = []
    
    nb_case = 0
    self.parameters = {}


    full_text = "\n".join(lines)
    in_prog = False
    prog = ""
    nb_prog = 0
    line_nb = 0
    nb_lines = len(lines)
    # parsing of the input file starts...
    for line in lines:
      line_nb = line_nb + 1
      line = clean_line(line)
      # while scanning a python section storing it...
      if ((line.find("#DECIM") > -1) or (line_nb == nb_lines)) and in_prog:
        t = "YALLA_prog_%d" % nb_prog
        self.direct_tag[t] = prog 
        self.direct_tag_ordered = self.direct_tag_ordered + [t]
        nb_prog = nb_prog + 1
        self.log_debug("prog python found in parametric file:\n%s" % prog, \
                       4, trace='PARAMETRIC_PROG,PARAMETRIC_PROG_DETAIL')
        in_prog = False
      # is it a program  enforced by #DECIM PYTHON directive?
      matchObj = re.match(r'^#DECIM\s*PYTHON\s*$', line)
      if (matchObj):
        in_prog = True
        prog = ""
        continue
      elif in_prog:
        prog = prog + line + "\n"
        continue
      # is it a tag enforced by #DECIM directive?
      if self.additional_tag(line):
        continue
      
      # if line void or starting with '#', go to the next line
      if len(line) == 0 or (line[0] == '#'):
        continue

      # parsing other line than #DECIM directive
      if not(tags_ok):
        # first line ever -> Containaing tag names
        tags_names = line.split(" ")
        tags_ok = True
        continue 

      line2scan = line
      for k in self.direct_tag.keys():
        line2scan = line2scan + " " + self.direct_tag[k]
        
      nb_case = nb_case + 1

      # if job case are filtered, apply it, jumping to next line if filter not match
      if self.args.parameter_filter:
        matchObj = re.match("^.*" + self.args.parameter_filter + ".*$", line2scan)
        if not(matchObj):
          continue

      if self.args.parameter_range and not(self.args.parameter_range == nb_case - 1):
        continue

      self.log_debug("testing : %s\ntags_names:%s" % (line, tags_names), \
                     4, trace='PARAMETRIC_DETAIL,PD')
    
      tags = shlex.split(line)

      if not(len(tags) == len(tags_names)):
        self.error("\tError : pb encountered in reading the test matrix file : %s " % self.args.parameter_file + \
                   "at  line \n\t\t!%s" % line + \
                   "\n\t\tless parameters to read than expected... Those expected are\n" + \
                   "\n\t\t\t %s " % ",".join(tags_names) + \
                   "\n\t\tand so far, we read" + \
                   "\n\t\t\t %s" % tag, exception=True, exit=True)
      
      ts = copy.deepcopy(tags_names)
      tag = {}
      self.log_debug("ts:%s\ntags:%s" % (pprint.pformat(ts), pprint.pformat(tags))\
                     , 4, trace='PARAMETRIC_DETAIL,PD')
      
      while(len(ts)):
        t = ts.pop(0)
        tag["%s" % t] = tags.pop(0)
        self.log_debug("tag %s : !%s! " % (t, tag["%s" % t]), 4, trace='PARAMETRIC_DETAIL,PD')
      self.log_debug('tag:%s' % pprint.pformat(tag), 4, trace='PARAMETRIC_DETAIL,PD')

      self.parameters[nb_case] = tag

    self.log_debug('self.parameters: %s ' % \
                     (pprint.pformat(self.parameters)), \
                     4, trace='PARAMETRIC_DETAIL,PD,PARAMETRIC')

    pd.options.display.max_rows = 999
    pd.options.display.max_columns = 999
    pd.options.display.width = 0
    pd.options.display.expand_frame_repr = True
    pd.options.display.max_columns = None

    
    l = pd.DataFrame(self.parameters).transpose()
    if len(l):
      tag = l.iloc[[0]]
    else:
      tag = {}
    self.log_debug('%d parameters before functional_tags : \n %s' % (len(l), l), \
                   4, trace='PARAMETRIC_DETAIL,PD')
    self.log_debug('tag before functional_tags : \n %s' % l.columns, \
                   4, trace='PARAMETRIC_DETAIL,PD')
    self.log_debug('prog before functional_tags : \n %s' % prog, \
                   4, trace='PARAMETRIC_DETAIL,PD')

    
    
    # evaluating parameter computed...
    
    if len(self.direct_tag):

      # first evaluation these parameter with the first combination of
      # parameter to check if they are unique or an array of values
      #
      # if unique, then evaluation remains to be done for all the
      #            possible combination
      # if arrays of values, its dimension  should be conformant to the set of
      #            combinations already known and that these values will complete

      
      self.log_debug('self.direct_tag %s tag:%s' % \
                   (pprint.pformat(self.direct_tag), pprint.pformat(tag)), \
                   4, trace='PARAMETRIC_DETAIL,PD')
      self.log_debug('self.direct_tag_ordered %s ' % \
                   (pprint.pformat(self.direct_tag_ordered)), \
                   4, trace='PARAMETRIC_DETAIL,PD')
      # adding the tags enforced by a #DECIM directive
      # evaluating them first

      # first path of evaluation for every computed tag
      
      for t in self.direct_tag_ordered:
        already_set_variables = ""
        if len(l) > 1:
          values = l.iloc[[1]]
          self.log_debug('values on first line : \n %s' % values, \
                         4, trace='PARAMETRIC_DETAIL,PD')
          for c in l.columns:
            already_set_variables = already_set_variables + "\n" + "%s = \"%s\" " % (c, l.iloc[0][c])
        self.log_debug('already_set_variables : \n %s' % already_set_variables, \
                       4, trace='PARAMETRIC_DETAIL,PD')

        formula = self.direct_tag[t]
        if t.find("YALLA_prog") == -1:
          results = { t:  self.eval_tag(t, formula, already_set_variables)}
          tag, result = t, results[t]
          self.log_debug('evaluated! %s = %s = %s' % (tag, formula, result), \
                         4, trace='PARAMETRIC_DETAIL,PD')
          # output produced is a row of values
          if isinstance(result, list):
            if  len(l) > 0 and (t in self.combined_tag):
              new_column = pd.DataFrame(pd.Series(result), columns=[t])
              self.log_debug('before cartesian product \n l: %d combinations : \n %s' % (len(l), l), \
                             4, trace='PARAMETRIC_DETAIL,PD')
              self.log_debug('before cartesian product \n new_column: %d combinations : \n %s' % (len(new_column), new_column), \
                             4, trace='PARAMETRIC_DETAIL,PD')
              l = self.cartesian(l, new_column)
              self.log_debug('after cartesian product %d combinations : \n %s' % (len(l), l), \
                             4, trace='PARAMETRIC_DETAIL,PD')
            else:
              if len(result) == len(l) or len(l) == 0:
                if len(l) > 0:
                  ser = pd.Series(result, index=l.index)
                else:
                  ser = pd.Series(result)
                l[t] = ser
              else:
                self.error(('parameters number mistmatch for expression' + \
                            '\n\t %s = %s \n\t --> ' + \
                            'expected %d and got %d parameters...') % \
                           (tag, formula, len(l), len(result)))
          else:
            # output produced is only one value -> computing it for all combination
            results = [result]
            for row in range(1, len(l)):
              values = l.iloc[[row]]
              self.log_debug('values on row %s: \n %s' % (row, values), \
                             4, trace='PARAMETRIC_DETAIL,PD')
              already_set_variables = ""
              for c in l.columns:
                already_set_variables = already_set_variables + "\n" + "%s = \"%s\" " % (c, l.iloc[row][c])
              self.log_debug('about to be revaluated! t=%s results=%s' % (t, results), \
                             4, trace='PARAMETRIC_DETAIL,PD')
              result = self.eval_tag(t, formula, already_set_variables)
              results = results + [result]
            self.log_debug('evaluated! %s = %s = %s' % (t, formula, results), \
                          4, trace='PARAMETRIC_DETAIL,PD')

            ser = pd.Series(results, index=l.index)
            l[t] = ser
        else:
          results = self.eval_tags(formula, already_set_variables)
          del self.direct_tag[t]

          # first updating all parameter that produces a vector
          result_as_column = {}
          for tag, result in results.items():  
            self.log_debug('evaluated! %s = %s = %s' % (tag, formula, result), \
                           4, trace='PARAMETRIC_DETAIL,PD')
            # output produced is a row of values
            if isinstance(result, list):
              if len(result) == len(l) or len(l) == 0 or (t in self.combined_tag):
                result_as_column[tag] = result
                ser = pd.Series(result, index=l.index)
                l[tag] = ser
              else:
                self.error(('parameters number mistmatch for parameter %s computed from a python section' + \
                            '\n\t expected %d and got %d parameters...') % \
                           (tag, len(l), len(result)))

          # second applying formula for all other variables and check that
          # row as column remains constant
          results_per_var = {}
          for v in results.keys():
            results_per_var[v] = [results[v]]
            
          for row in range(1, len(l)):
            
            values = l.iloc[[row]]
            self.log_debug('values on row %s: \n %s' % (row, values), \
                           4, trace='PARAMETRIC_PROG_DETAIL')
            already_set_variables = ""
            for c in l.columns:
              already_set_variables = already_set_variables + "\n" + "%s = \"%s\" " % (c, l.iloc[row][c])
            results_for_this_row = self.eval_tags(formula, already_set_variables)
            for v in results.keys():
              results_per_var[v] = results_per_var[v] + [results_for_this_row[v]]
              if (v in result_as_column.keys()):
                if not(cmp(result_as_column[v], results_for_this_row[v]) == 0):
                  self.error('mismatch in parameter list  computed from file %s \n\tfor parameter %s: ' % \
                             (self.args.parameter_file, v) + \
                             '\n\t    returned %s for first combination ' % result_as_column[v] + \
                             '\n\tbut returned %s for %dth combination ' % (results_for_this_row[v], row),
                             exit=True, where='read_parameter_file', exception=False)

            self.log_debug('evaluated! for row %s = %s' % (row, pprint.pformat(results_for_this_row)), \
                           4, trace='PARAMETRIC_PROG_DETAIL')

          for v in results.keys():
            if not(v in result_as_column.keys()):
              ser = pd.Series(results_per_var[v], index=l.index)
              l[v] = ser

    # forcing integer casting of SLURM Integer parameters

    columns_to_cast = []
    for p in l.columns:
        if p in self.slurm_vars.keys():
            if self.slurm_vars[p]==int:
                self.log_debug('casting parameter %s to int' % p,\
                   4, trace='PS,PARAMETRIC_DETAIL,PD,PARAMETRIC_SUMMARY')
                columns_to_cast = columns_to_cast + [p]
    if len(columns_to_cast):
        l[columns_to_cast] = l[columns_to_cast].astype(int)

    l['current_combination'] =  range(0, len(l))

    if self.args.parameter_count:
        parameter_count = '%d combination of %d parameters   ' % (len(l), len(l.columns))
        self.log_console(parameter_count)

    if self.args.parameter_list:
        if self.args.parameter_sort:
            sorting_parameters = [ x.replace("~","") for x in self.args.parameter_sort.split(",")]
            sorting_ascending = [ x.find("~")==-1 for x in self.args.parameter_sort.split(",")]
            self.log_debug("sorting_parameters=%s,sorting_ascending=%s" % (sorting_parameters,sorting_ascending),\
                       4, trace='PS,PARAMETRIC_DETAIL,PD,PARAMETRIC_SUMMARY')
            l = l.sort_values(by=sorting_parameters, ascending=sorting_ascending)
        if self.args.parameter_format:
            l.drop('current_combination', axis=1, inplace=True)
            parameter_list = '%s' % (l.to_string(index=False))
            print(parameter_list)
        else:
            parameter_list = '%d combination of %d parameters  : l \n %s' % (len(l), len(l.columns), l)
            self.log_console(parameter_list)
 
        self.log_debug(parameter_list,\
                       4, trace='PS,PARAMETRIC_DETAIL,PD,PARAMETRIC_SUMMARY')


    self.array_clustered = []
    clustering_criteria = []
    for c in ['nodes','ntasks','ntasks_per_node','time']:
        if c in l.columns:
            clustering_criteria.append(c)

    cluster_keys = ",".join(map(lambda x:str(x),clustering_criteria))
    self.log_debug('critera taken : (%s) from %s' %  (cluster_keys,l.columns), \
                   4, trace='PARAMETRIC_DETAIL,PD,GATHER_JOBS,GJ')


    if len(clustering_criteria):
      job_per_node_number = l.groupby(clustering_criteria).size()
      # print job_per_node_number
      # for j in job_per_node_number.keys():
      #   print j,':',job_per_node_number[j]
      l_per_clusters = l.groupby(clustering_criteria).size()
      self.log_debug('cluster (%s) in %s combinations:' % \
                     (cluster_keys,len(l_per_clusters)), \
                     4, trace='PARAMETRIC_DETAIL,PD,GATHER_JOBS,GJ')

      for n in l_per_clusters.index:
          criteria = clustering_criteria
          if (isinstance(n, type(8))):
              n = [n]
          subset = l.loc[l[criteria[0]]==n[0]]
          values = {}
          values[criteria[0]]=n[0]
          i = 1
          while i<len(criteria):
              subset = subset.loc[l[criteria[i]]==n[i]]
              values[criteria[i]]=n[i]
              i = i+1
              
          subset = subset.filter(items=clustering_criteria)
          concerned_array_ids = str(RangeSet(','.join(map(lambda x:str(x),list(subset.index)))))
          values['array'] = concerned_array_ids
          
          self.array_clustered = self.array_clustered + \
                                 [values]
                                  
          self.log_debug('\n%s' % pprint.pformat(subset),\
                         4, trace='PARAMETRIC_DETAIL,PD,GATHER_JOBS,GJ')
                         
      self.log_info('array_clusters: %s' % pprint.pformat( self.array_clustered),
                    1, trace='PARAMETRIC_DETAIL,PD,GATHER_JOBS,GJ')
      

    if self.args.parameter_list or self.args.parameter_count:
        sys.exit(0)

    self.parameters = l
    return self.array_clustered
      
