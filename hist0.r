setwd("~/PyeMovements/")

require(ggplot2)
library(doSNOW)
library(foreach)

cl<-makeCluster(16)
registerDoSNOW(cl)

timers = as.integer(10^seq(2,5,.1))
data = foreach(timer=timers,.combine=rbind) %dopar% {
  system(paste0("python antisaccade.py --max-trials ", as.integer(timer)))
  return(read.delim(sprintf("latencies-%d-%.2f-%.2f-%.2f-%.2f.txt",timer,.250,.180,0,0),sep="\t",header=F))
}
colnames(data) = c("max_trials","timer_mean","labile_mean","gap_cancel_prob","cue_cancel_prob","latency")
write.table(data,"sim_trials.dat",sep="\t",row.names=F,col.names=T)

stopCluster(cl)

system("rm latencies*")