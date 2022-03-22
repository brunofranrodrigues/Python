import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

caminho = "{}//files//01-09-2021-full.csv".format(os.path.dirname(__file__))

#Tarefa 1
data_frame = pd.read_csv(caminho, usecols=["Operating System", "Client Version", "Status", "Server Name"])

print(data_frame)

dados_agrupados = data_frame.groupby("Server Name").size() #agrupando e contando
#grafico_barras = dados_agrupados.plot.bar() #gerando o gráfico a partir dos dados
#plt.show()

dados_agrupados.to_csv("servidor.csv")



#arquivo = grafico_barras.get_figure()
#arquivo.savefig("grafico_tipos.jpg")
#grafico_barras.get_figure().savefig("grafico_tipos.jpg")
#data_frame.groupby("Type 1").size().plot.bar().get_figure().savefig("grafico_tipos.jpg")
