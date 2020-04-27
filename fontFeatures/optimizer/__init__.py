from .Routine import optimizations as routine_optimizations

class Optimizer:
  def optimize(self, ff):
    for r in ff.routines:
      self.optimize_routine(r)
      for k,v in self.features.items():
        f = feaast.FeatureBlock(k)
        for n in v:
          if isinstance(n, Routine):
            self.optimize_routine(n)

  def optimize_routine(self, r):
    for optimization in routine_optimizations:
      optimization().apply(r)
