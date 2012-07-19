import os
import re

class DependencyError(Exception): pass

def get_all_modules(path):
  modules = {}
  for root, folders, files in os.walk(path):
    current_folder = root.replace(path, "").strip(os.sep)
    current_folder = current_folder.split(os.sep)
    current_module = ".".join(current_folder)
    for fname in files:
      abs_filename = root + os.sep + fname
      if fname.endswith(".coffee"):
        if not current_module:
          module_name = fname[:-7]
        else:
          if fname == current_folder[-1] + ".coffee":
            module_name = current_module
          else:
            module_name = current_module + "." + fname[:-7]

        modules[module_name] = abs_filename

  return modules

_require_regex = re.compile(r"#require ([a-zA-Z_][a-zA-Z0-9_.]*)")
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
    depended_modules = backdeps.get(module_name, [])
    for mn in depended_modules:
      foredeps[mn].remove(module_name)
      if len(foredeps[mn]) == 0:
        s.append(mn)

  if sum([len(x) for x in foredeps.values()]) > 0:
    raise DependencyError("There's a cycle in your code: %s" % foredeps)
  else:
    return sortedmodules, modules
