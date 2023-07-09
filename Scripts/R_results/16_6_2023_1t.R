###tables of todo a mano 
# Instala los paquetes si no los tienes instalados

# Carga los paquetes
library(readxl)
library(tidyverse)

# Especifica la ruta de tu archivo de Excel
excel_file <- "16_6_2023_1t_R.xlsx"

# Lee la hoja de Excel
sheet_name <- "OD_IPTG"  # Reemplaza con el nombre de la hoja real
OD_IPTG <- read_excel(excel_file, sheet = sheet_name)
OD_ATC <- read_excel(excel_file, sheet = 'OD_ATC')
GFP_IPTG <- read_excel(excel_file, sheet = 'GFP_IPTG')
GFP_ATC <- read_excel(excel_file, sheet = 'GFP_ATC')
KATE_IPTG <- read_excel(excel_file, sheet = 'KATE_IPTG')
KATE_ATC <- read_excel(excel_file, sheet = 'KATE_ATC')



normalize_protein_inductor <- function(protein_inductor, OD_inductor, inductor_label) {
  #***
  #This function  normalises as a celular ratio  
  #***
  
  s=paste(inductor_label, "0", sep = " ")
  df_norm <- data.frame(Time = protein_inductor$Time , "0" = rep(0, nrow(protein_inductor)))
  
  for (col in names(protein_inductor)[-1]) {
    col_name <- col
    new_col <- (protein_inductor[[col]] / OD_inductor[[paste0(col)]]) - (protein_inductor[[s]] / OD_inductor[[s]])
    df_norm <- cbind(df_norm, new_col)
  }
  
  df_norm <- df_norm[, -2]
  
  col_names <- c("Time", paste0(inductor_label, " ", gsub(paste0(inductor_label, " "), "", names(protein_inductor)[-1])))
  colnames(df_norm) <- col_names
  
  df_norm[1, ] <- rep(0, ncol(df_norm))
  df_mean= df_norm %>%
    group_by(Time) %>%
    summarise(across(starts_with(inductor_label), mean))
  df_sd= df_norm %>%
    group_by(Time) %>%
    summarise(across(starts_with(inductor_label), sd))
  
  
  return(list(df_norm = df_norm, df_mean = df_mean, df_sd = df_sd))
  
}

result=normalize_protein_inductor(GFP_IPTG,OD_IPTG,"IPTG")
df_norm_GFP_IPTG=result$df_norm
df_mean_GFP_IPTG=result$df_mean
df_sd_GFP_IPTG=result$df_sd

# GFP IPTG
require(ggplot2)
require(RColorBrewer)
# Create a function to generate darker shades from the "Blues" palette
get_darker_blues <- colorRampPalette(brewer.pal(8, "Blues")[2:8])
# Obtain the darker shades of blue
my_colors <- get_darker_blues(num_colors)
GFP_IPTG_normalization <- ggplot(df_mean_GFP_IPTG, aes(x = Time)) +
  geom_line(aes(y = `IPTG 0`, color = "0"), linetype = "solid", size = 1.3) +
  geom_smooth(aes(y = `IPTG 0`, color = "0"), method = "loess", se = FALSE, size = 1.3) +
  geom_smooth(aes(y = `IPTG 0.078125`, color = "0.078125"), method = "loess", se = FALSE, size = 1.3) +
  geom_smooth(aes(y = `IPTG 0.078125`, color = "0.078125"), method = "loess", se = FALSE, size = 1.3) +
  geom_smooth(aes(y = `IPTG 0.15625`, color = "0.15625"), method = "loess", se = FALSE, size = 1.3) +
  geom_smooth(aes(y = `IPTG 0.3125`, color = "0.3125"), method = "loess", se = FALSE, size = 1.3) +
  geom_smooth(aes(y = `IPTG 0.625`, color = "0.625"), method = "loess", se = FALSE, size = 1.3) +
  geom_smooth(aes(y = `IPTG 1.25`, color = "1.25"), method = "loess", se = FALSE, size = 1.3) +
  geom_smooth(aes(y = `IPTG 2`, color = "2"), method = "loess", se = FALSE, size = 1.3) +
  geom_smooth(aes(y = `IPTG 2.5`, color = "2.5"), method = "loess", se = FALSE, size = 1.3) + 
  ##append geom_errorbar
  geom_errorbar(aes(ymin = `IPTG 0` - df_sd_GFP_IPTG$`IPTG 0`,
                    ymax = `IPTG 0` + df_sd_GFP_IPTG$`IPTG 0`,
                    color = "0"), width = 0.2) +
  geom_errorbar(aes(ymin = `IPTG 0.078125` - df_sd_GFP_IPTG$`IPTG 0.078125`,
                    ymax = `IPTG 0.078125` + df_sd_GFP_IPTG$`IPTG 0.078125`,
                    color = "0.078125"), width = 0.2) +
  geom_errorbar(aes(ymin = `IPTG 0.15625` - df_sd_GFP_IPTG$`IPTG 0.15625`,
                    ymax = `IPTG 0.15625` + df_sd_GFP_IPTG$`IPTG 0.15625`,
                    color = "0.15625"), width = 0.2) +
  geom_errorbar(aes(ymin = `IPTG 0.3125` - df_sd_GFP_IPTG$`IPTG 0.3125`,
                    ymax = `IPTG 0.3125` + df_sd_GFP_IPTG$`IPTG 0.3125`,
                    color = "0.3125"), width = 0.2) +
  geom_errorbar(aes(ymin = `IPTG 0.625` - df_sd_GFP_IPTG$`IPTG 0.625`,
                    ymax = `IPTG 0.625` + df_sd_GFP_IPTG$`IPTG 0.625`,
                    color = "0.625"), width = 0.2) +
  geom_errorbar(aes(ymin = `IPTG 1.25` - df_sd_GFP_IPTG$`IPTG 1.25`,
                    ymax = `IPTG 1.25` + df_sd_GFP_IPTG$`IPTG 1.25`,
                    color = "1.25"), width = 0.2) +
  geom_errorbar(aes(ymin = `IPTG 2` - df_sd_GFP_IPTG$`IPTG 2`,
                    ymax = `IPTG 2` + df_sd_GFP_IPTG$`IPTG 2`,
                    color = "2"), width = 0.2) +
  geom_errorbar(aes(ymin = `IPTG 2.5` - df_sd_GFP_IPTG$`IPTG 2.5`,
                    ymax = `IPTG 2.5` + df_sd_GFP_IPTG$`IPTG 2.5`,
                    color = "2.5"), width = 0.2) +
  scale_y_continuous(breaks = seq(-30, 100, 10),limits=c(-30,100)) +
  scale_color_brewer(palette = "Set3") + 
  #scale_color_manual(values = my_colors) + 
  
  labs(x = "Time (h)",
       y =  bquote(bold("msfGFP Fluorescence ratio (RFU / OD"[600~nm]~.(")"))),
       color = "[IPTG] (mM)") + 
 theme_light() + 
  theme(plot.title = element_text(face = "bold", hjust = 0.5),
        axis.title = element_text(face = "bold"),
        legend.title=element_text(face="bold"),
        legend.position = "bottom"
        )# + 
# ylim(-15,70)

print(GFP_IPTG_normalization)

ggsave("17_6_2023_toggle_switch_GFP_IPTG_normalization__1_transfer_plot.png", plot = GFP_IPTG_normalization, width = 5,height = 4.50,units = "in",dpi = 500)

