from .Routine import optimizations as routine_optimizations
import fontFeatures

class Optimizer:
  def optimize(self, ff):
    for r in ff.routines:
      self.optimize_routine(r)
      for k,v in ff.features.items():
        for n in v:
          if isinstance(n, fontFeatures.Routine):
            self.optimize_routine(n)

  def optimize_routine(self, r):
    for optimization in routine_optimizations:
      optimization().apply(r)