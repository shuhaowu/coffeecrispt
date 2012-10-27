import os
import re
import sys

class DependencyError(Exception): pass

_namespace_regex = re.compile(r"namespace[ (][\"']([a-zA-Z_][a-zA-Z0-9_.]*)[\"'][)]{0,1}")
def get_all_modules(path):
  modules = {}
  for root, folders, files in os.walk(path):
    current_folder = root.replace(path, "").strip(os.sep)
    current_folder = current_folder.split(os.sep)
    current_module = ".".join(current_folder)
    for fname in files:
      abs_filename = root + os.sep + fname

      if fname.endswith(".coffee"):
        with open(abs_filename) as f: # override
          content = f.read()
          n = _namespace_regex.search(content)
          if n:
            module_name = n.group(1)
          else:
            module_name = None

        if not module_name:
          if not current_module:
            module_name = fname[:-7]
          else:
            if fname == current_folder[-1] + ".coffee":
              module_name = current_module
            else:
              module_name = current_module + "." + fname[:-7]

        modules[module_name] = abs_filename

  return modules

_require_regex = re.compile(r"require[ (][\"']([a-zA-Z_][a-zA-Z0-9_.]*)[\"'][)]{0,1}")
def get_dep(path):
  with open(path) as f:
    content = f.read()
    return _require_regex.findall(content)

def get_all_modules_sorted(path): # Algorithm of topsort adapted from wikipedia's article on topsort
  modules = get_all_modules(path)
  foredeps = {} # module : list of modules depended on this module
  backdeps = {} # module : list of modules that's requird by this module

  sortedmodules = []
  s = []

  for module_name, absfilepath in modules.iteritems():
    _t = get_dep(absfilepath)
    foredeps[module_name] = _t
    if len(_t) == 0:
      s.append(module_name)
    else:
      for mn in _t:
        d = backdeps.get(mn, [])
        d.append(module_name)
        backdeps[mn] = d

  while len(s) > 0:
    module_name = s.pop()
    sortedmodules.append(module_name)
    modules_depended = backdeps.get(module_name, [])
    for mn in modules_depended:
      foredeps[mn].remove(module_name)
      if len(foredeps[mn]) == 0:
        s.append(mn)

  if sum([len(x) for x in foredeps.values()]) > 0:
    print >> sys.stderr, "There's a cycle or an unsatisfied dep in your code!"
    for x in foredeps:
      if len(foredeps[x]) > 0:
        print >> sys.stderr, "Module '%s' depends on %s but are not found!" % (x, foredeps[x])
        break
    raise DependencyError("Dependency Unsatisfied. There may be other dep problems, but fix this first!")
  else:
    return sortedmodules, modules
