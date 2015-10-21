setwd("~/PyeMovements/")

require(plyr)
require(rhdf5)
require(ggplot2)
require(parallel)
require(data.table)

d = h5read("results.h5","points",compoundAsDataFrame=FALSE)

dd = rbindlist(mclapply(1:length(d$latencies$labile_mean), function(x, z) {
  .d = data.table(density=density(z$latencies[,x],n=200,from=0,to=2)$y)
  .d[,point:=x]
  .d
}, d$latencies, mc.co))