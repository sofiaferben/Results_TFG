 ###create Boxplot at OD0 
# Instala los paquetes si no los tienes instalados
# Carga los paquetes
library(readxl)
library(tidyverse)

# Especifica la ruta de tu archivo de Excel
excel_file <- "8_6_2023_R.xlsx"
OD_IPTG_mano <- read_excel(excel_file, sheet = 'OD_IPTG')
OD_ATC_mano <- read_excel(excel_file, sheet = 'OD_ATC')
excel_file <- "20_6_2023_R.xlsx"
OD_IPTG_OT2 <- read_excel(excel_file, sheet = 'OD_IPTG')
OD_ATC_OT2 <- read_excel(excel_file, sheet = 'OD_ATC')

OD_IPTG_mano_0 <- subset(OD_IPTG_mano, Time == 0)
OD_IPTG_mano_0 <- select(OD_IPTG_mano_0, -"Time")

OD_ATC_mano_0 <- subset(OD_ATC_mano, Time == 0)
OD_ATC_mano_0 <- select(OD_ATC_mano_0, -"Time")

OD_IPTG_OT2_0 <- subset(OD_IPTG_OT2, Time == 0)
OD_IPTG_OT2_0 <- select(OD_IPTG_OT2_0, -"Time")

OD_ATC_OT2_0 <- subset(OD_ATC_OT2, Time == 0)
OD_ATC_OT2_0 <- select(OD_ATC_OT2_0, -"Time")

#para poder hacer el merge aunque luego perdamos informacion de la ocnentracion de cada uno de los inductores
column_names <- colnames(OD_IPTG_mano_0)
colnames(OD_ATC_mano_0) <- column_names
colnames(OD_ATC_OT2_0) <- column_names

# Combina los cuatro dataframes en uno solo
combined_df <- rbind(OD_IPTG_mano_0, OD_ATC_mano_0, OD_IPTG_OT2_0, OD_ATC_OT2_0)

# Agrega una columna para identificar la fuente de los datos
combined_df$Fuente <- rep(c("IPTG hand control", "ATC hand control", "IPTG OT2", "ATC OT2"), each = nrow(combined_df)/4)


# Realiza la transformación de las columnas en variables usando pivot_longer()
combined_df_long <- combined_df %>%
  pivot_longer(cols = -Fuente, names_to = "Columna", values_to = "Valor")

# Agregar las columnas inductor y condition al dataframe combined_df_long
combined_df_long <- combined_df_long %>%
  mutate(inductor = ifelse(Fuente %in% c("IPTG hand control", "IPTG OT2"), "IPTG", "ATC"),
         Condition = ifelse(Fuente %in% c("IPTG hand control", "ATC hand control"), "Manual", "OT2"))



# 
# # Crea la gráfica de boxplots
# colors = c( "#440154FF","#1565c0")
# library(ggplot2)
# 
# colors <- c("#440154FF", "#1565c0")
# 
# boxplot <- ggplot(combined_df_long, aes(x = Fuente, y = Valor, color = Condition, fill = Condition)) +
#   geom_boxplot(alpha = 0.3) +
#   labs(x = "Inductor", y = "Valores") +
#   scale_colour_manual(values = colors) +
#   scale_fill_manual(values = colors)
# 
# print(boxplot)

library(ggplot2)

colors <- c("#440154FF", "#1565c0")

boxplot <- ggplot(combined_df_long, aes(x = Fuente, y = Valor, fill = Condition ,color=Condition)) +
  geom_boxplot(alpha = 0.2) +
  scale_fill_manual(values = colors, labels = c("Manual", "OT2")) +
  scale_color_manual(values = colors, labels = c("Manual", "OT2")) +
  facet_wrap(~ inductor, ncol = 2, scales = "free_x", strip.position = "bottom") +
  ylab('OD') + 
  xlab('Condition') + 
 scale_x_discrete(name = NULL, breaks = NULL) + # these lines are optional
  theme(legend.position = "right",
        ) 
print(boxplot)

ggsave("boxplot.png", plot = boxplot, dpi = 500)
