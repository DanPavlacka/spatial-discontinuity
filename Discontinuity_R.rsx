##scripts=group
##Layer=vector
##X=Field Layer
##Y=Field Layer
##col=Field Layer
##output_plots_to_html




library(ggplot2)

Q <- quantile(Layer[[Y]], probs=c(.25, .75), na.rm = T)
iqr <- IQR(Layer[[Y]], na.rm = T)
up <-  Q[2]+1.5*iqr 
low<- Q[1]-1.5*iqr 

Layer <- subset(Layer,Layer[[Y]]  > (Q[1] - 1.5*iqr) & Layer[[Y]] < (Q[2]+1.5*iqr))


p <-ggplot(Layer, aes(x=Layer[[X]], y=Layer[[Y]], color=Layer[[col]])) +
    geom_point(color = "black") + 
    geom_smooth(method=lm, se=FALSE, fullrange=F)

p+scale_color_brewer(palette="Dark2")
