setwd("~/PyeMovements/")

require(ggplot2)
library(doSNOW)
library(foreach)

cl<-makeCluster(16)
registerDoSNOW(cl)

timers = seq(.1,1.0,.05)
data = foreach(timer=timers,.combine=rbind) %dopar% {
  system(paste0("python antisaccade.py --max-trials 100000 --timer_mean ", timer))
  return(read.delim(sprintf("latencies-%.2f-%.2f-%.2f-%.2f.txt",timer,.180,0,0),sep="\t",header=F))
}
colnames(data) = c("timer_mean","labile_mean","gap_cancel_prob","cue_cancel_prob","latency")
write.table(data,"sim_timer.dat",sep="\t",row.names=F,col.names=T)

stopCluster(cl)

system("rm latencies*")