###tahbes of todo a mano 
# Instala los paquetes si no los tienes instalados

# Carga los paquetes
library(readxl)
library(tidyverse)

# Especifica la ruta de tu archivo de Excel
excel_file <- "8_6_2023_R.xlsx"

# Lee la hoja de Excel
sheet_name <- "OD_IPTG"  # Reemplaza con el nombre de la hoja real
OD_IPTG <- read_excel(excel_file, sheet = sheet_name)
OD_ATC <- read_excel(excel_file, sheet = 'OD_ATC')
GFP_IPTG <- read_excel(excel_file, sheet = 'GFP_IPTG')
GFP_ATC <- read_excel(excel_file, sheet = 'GFP_ATC')
KATE_IPTG <- read_excel(excel_file, sheet = 'KATE_IPTG')
KATE_ATC <- read_excel(excel_file, sheet = 'KATE_ATC')
# 
# 
# # 1) MedIAS OD_IPTG
# mean_OD_IPTG <- OD_IPTG %>%
#   group_by(Time) %>%
#   summarise(across(starts_with("IPTG"), mean))
# 
# # Muestra el dataframe con las medias
# print(mean_OD_IPTG)
# 
# 
# # Calcula las medias por tiempo y etiqueta
# SD_OD_IPTG <- OD_IPTG %>%
#   group_by(Time) %>%
#   summarise(across(starts_with("IPTG"), sd))
# 
# # Muestra el dataframe con las medias
# print(SD_OD_IPTG)
# 
# #2) OD_ATC
# 
# mean_OD_ATC <- OD_ATC %>%
#   group_by(Time) %>%
#   summarise(across(starts_with("ATC"), mean))
# 
# # Muestra el dataframe con las medias
# print(mean_OD_ATC)
# 
# 
# # Calcula las medias por tiempo y etiqueta
# SD_OD_ATC <- OD_ATC %>%
#   group_by(Time) %>%
#   summarise(across(starts_with("ATC"), sd))
# 
# # Muestra el dataframe con las medias
# print(SD_OD_ATC)
# 
# 
# #3) GFP IPTG
# mean_GFP_IPTG <- GFP_IPTG %>%
#   group_by(Time) %>%
#   summarise(across(starts_with("IPTG"), mean))
# 
# # Muestra el dataframe con las medias
# print(mean_GFP_IPTG)
# 
# 
# # Calcula las medias por tiempo y etiqueta
# SD_GFP_IPTG <- GFP_IPTG %>%
#   group_by(Time) %>%
#   summarise(across(starts_with("IPTG"), sd))
# 
# # Muestra el dataframe con las medias
# print(SD_GFP_IPTG)
# 
# 
# #4) GFP ATC
# 
# mean_GFP_ATC <- GFP_ATC %>%
#   group_by(Time) %>%
#   summarise(across(starts_with("ATC"), mean))
# 
# # Muestra el dataframe con las medias
# print(mean_GFP_ATC)
# 
# 
# # Calcula las medias por tiempo y etiqueta
# SD_GFP_ATC <- GFP_ATC %>%
#   group_by(Time) %>%
#   summarise(across(starts_with("ATC"), sd))
# 
# # Muestra el dataframe con las medias
# print(SD_GFP_ATC)
# 
# #5) KATE IPTG
# 
# mean_KATE_IPTG <- KATE_IPTG %>%
#   group_by(Time) %>%
#   summarise(across(starts_with("IPTG"), mean))
# 
# # Muestra el dataframe con las medias
# print(mean_KATE_IPTG)
# 
# 
# # Calcula las medias por tiempo y etiqueta
# SD_KATE_IPTG <- KATE_IPTG %>%
#   group_by(Time) %>%
#   summarise(across(starts_with("IPTG"), sd))
# 
# # Muestra el dataframe con las medias
# print(SD_KATE_IPTG)
# 
# 
# 
# #6) KATE ATC
# 
# mean_KATE_ATC <- KATE_ATC %>%
#   group_by(Time) %>%
#   summarise(across(starts_with("ATC"), mean))
# 
# # Muestra el dataframe con las medias
# print(mean_KATE_ATC)
# 
# 
# # Calcula las medias por tiempo y etiqueta
# SD_KATE_ATC <- KATE_ATC %>%
#   group_by(Time) %>%
#   summarise(across(starts_with("ATC"), sd))
# 
# # Muestra el dataframe con las medias
# print(SD_KATE_ATC)


# 
# ####GFP IPTG NORMALIZACION 
# 
# ###Medias
# df_norm_GFP_IPTG_mean <- data.frame(Time = mean_GFP_IPTG$Time, 'IPTG 0' = rep(0, nrow(mean_GFP_IPTG)))
# 
# for (col in names(mean_GFP_IPTG)[-1]) {
#   col_name <- col
#   new_col <- (mean_GFP_IPTG[[col]] / mean_OD_IPTG[[paste0(col)]]) - (mean_GFP_IPTG$'IPTG 0' / mean_OD_IPTG$"IPTG 0")
#   df_norm_GFP_IPTG_mean <- cbind(df_norm_GFP_IPTG_mean, new_col)
# }
# 
# df_norm_GFP_IPTG_mean <- df_norm_GFP_IPTG_mean[, -2]
# 
# col_names <- c("Time", paste0("IPTG_", gsub("IPTG ", "", names(mean_GFP_IPTG)[-1])))
# colnames(df_norm_GFP_IPTG_mean) <- col_names
# 
# df_norm_GFP_IPTG_mean[1, ] <- rep(0, ncol(df_norm_GFP_IPTG_mean))
# 

# 
# ###ESTO NO FUNCIONA MAÑANA TOCALO
# 
# normalize_protein_inductor <- function(mean_protein_inductor, mean_OD_inductor, inductor_label) {
#   #.....
#   #funciona toma como dataframes las medias a cada tiempo 
#   #.....
#   s=paste(inductor_label, "0", sep = " ")
#   df_norm <- data.frame(Time = mean_protein_inductor$Time , "0" = rep(0, nrow(mean_protein_inductor)))
#   
#   for (col in names(mean_protein_inductor)[-1]) {
#     col_name <- col
#     new_col <- (mean_protein_inductor[[col]] / mean_OD_inductor[[paste0(col)]]) - (mean_protein_inductor[[s]] / mean_OD_inductor[[s]])
#     df_norm <- cbind(df_norm, new_col)
#   }
# 
# df_norm <- df_norm[, -2]
# 
# col_names <- c("Time", paste0(inductor_label, " ", gsub(paste0(inductor_label, " "), "", names(mean_protein_inductor)[-1])))
# colnames(df_norm) <- col_names
# 
# df_norm[1, ] <- rep(0, ncol(df_norm))
# 
#   return(df_norm)
# }


normalize_protein_inductor_v2 <- function(protein_inductor, OD_inductor, inductor_label) {
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
    summarise(across(starts_with("IPTG"), mean))
  df_sd= df_norm %>%
    group_by(Time) %>%
    summarise(across(starts_with("IPTG"), sd))
  
  
  return(list(df_norm = df_norm, df_mean = df_mean, df_sd = df_sd))

}

result=normalize_protein_inductor_v2(GFP_IPTG,OD_IPTG,"IPTG")
df_norm_GFP_IPTG=result$df_norm
df_mean_GFP_IPTG=result$df_mean
df_sd_GFP_IPTG=result$df_sd














