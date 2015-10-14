setwd("~/PyeMovements/")

require(ggplot2)
library(doSNOW)
library(foreach)

cl<-makeCluster(16)
registerDoSNOW(cl)

timers = seq(.02,.4,.02)
data = foreach(timer=timers,.combine=rbind) %dopar% {
  system(paste0("python antisaccade.py --max-trials 100000 --labile_mean ", timer))
  return(read.delim(sprintf("latencies-%.2f-%.2f-%.2f-%.2f.txt",.250,timer,0,0),sep="\t",header=F))
}
colnames(data) = c("timer_mean","labile_mean","gap_cancel_prob","cue_cancel_prob","latency")
write.table(data,"sim_labile.dat",sep="\t",row.names=F,col.names=T)

stopCluster(cl)

system("rm latencies*")