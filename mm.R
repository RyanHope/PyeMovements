setwd("~/PyeMovements/")

require(plyr)
require(rhdf5)
require(ggplot2)
require(parallel)
require(data.table)
require(reshape2)

d = h5read("~/PyeMovements/results.h5","points",compoundAsDataFrame=FALSE)

all_summary = fread(tail(list.files("/CogWorks/Projects/SaccadeTask/",pattern="^summary_|\\.dat$",full.names=T),1))
all_summary[,correct:=ifelse(saccade.response.target.correct,
                             paste(mode,"correct",sep="-"),
                             paste(mode,"incorrect",sep="-"))]
all_summary_clean = all_summary[average.quality==1 & !is.na(first.saccade.latency)]

dd = rbindlist(mclapply(1:length(d$latencies$labile_mean), function(x, z, zz) {
  .ks = ks.test(zz[sid=="0304b"&correct=="pro-correct",first.saccade.latency]*1000,z$latencies[,x])
  data.table(
    id=x,
    timer_states=z$timer_states[x],
    timer_mean1=z$timer_mean1[x],
    timer_mean2=z$timer_mean2[x],
    timer_mean3=z$timer_mean3[x],
    labile_mean=z$labile_mean[x],
    labile_stdev=z$labile_stdev[x],
    cue_cancel_prob=z$cue_cancel_prob[x],
    ks.stat=.ks$statistic,
    ks.p=.ks$p.value
  )
}, d$latencies, all_summary_clean, mc.cores=12))
dd[order(ks.stat),]

#data=density(all_summary_clean[sid="e35da"&correct=="pro-correct",first.saccade.latency]*1000,from=0,to=1000)
id = 421937
.den = data.table(
  latency = c(all_summary_clean[sid=="0304b"&correct=="pro-correct",first.saccade.latency]*1000,
              sample(d$latencies$latencies[,id],150)),
  model = c(rep("data",all_summary_clean[sid=="0304b"&correct=="pro-correct",.N]),rep("model",150))
)

ggplot(melt(.den,id.var="freq",value.name="density")) + 
  geom_line(aes(x=freq,y=density,color=variable,group=variable))