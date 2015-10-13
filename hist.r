setwd("c:/Users/rmh30_000/workspace/PyeMovements/")

require(ggplot2)
library(doSNOW)
library(foreach)

cl<-makeCluster(8)
registerDoSNOW(cl)

timers = seq(.1,1.0,.05)
data = foreach(timer=timers,.combine=rbind) %dopar% {
  system(paste0("python antisaccade.py --max-trials 1000000 --timer_mean ", timer))
  return(read.delim(sprintf("latencies-%.2f.txt",timer),sep="\t",header=F))
}
colnames(data) = c("timer_mean","latency")
write.table(data,"sim_timer_mean_100ms-1000ms-50ms_1000000.dat",sep="\t",row.names=F,col.names=T)

ggplot(data[data$latency<1.5,]) + 
  geom_line(aes(x=latency,group=timer_mean,color=timer_mean),stat="density",size=1.25) +
  


stopCluster(cl)