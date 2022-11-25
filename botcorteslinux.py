import json
import requests
from colorama import Fore, Style
import time, datetime
import paramiko as pm
from mailgmail import *
import os
class AllowAllKeys(pm.MissingHostKeyPolicy):
    def missing_host_key(self, client, hostname, key):
        return

def pedir():
    global analisis, deudores, nodeudores, total, ParaCortar
    analisis = ""
    os.system('clear')
    limpiar()
    veces = 0
#    ResultadoFinal = ""
 
    while True:
        #pido 50 y los limpio
        resp = requests.get(url1+str(veces), headers=headers)
        RESULTADO = json.dumps(resp.json(), indent=4)
        #print(RESULTADO)
        RESULTADO = json.loads(RESULTADO)
        if len(RESULTADO) == 50:
            analizar(RESULTADO)
            veces +=50 #para pedir los proximos 50
        if len(RESULTADO) < 50:
            analizar(RESULTADO)
            break
    guardarcorte()
    #print(analisis)
    #print(ParaCortar)
    print (Fore.YELLOW + "__ Total deudores:",deudores )
    print (Fore.GREEN + "__ Total sin deudas:",nodeudores )
    print (Fore.CYAN + "__ Total abonados:",str(total))

def analizar(limp2):
    global analisis, deudores, nodeudores, total
    global ParaCortar
   # deudores = 0
   # nodeudores = 0
    

    total += len(limp2)
    for x in range(len(limp2)):
            #print (limp2[x]["riesgoalcanzado"])
            deuda = limp2[x]["riesgoalcanzado"]
            
            if deuda > 0:
                deudores += 1
                #print (Fore.RED + "▓ El usuario", limp2[x]["nombre"], "Debe",deuda)
                nombre = str(limp2[x]["nombre"]).replace(" ", "_")
                analisis = analisis + Fore.RED + ("El usuario " + nombre + " Debe " + str(deuda) + "\n")
                corte = str(limp2[x]["observaciones"])
                correo = str(limp2[x]["email"])
                if corte == '':
                    corte = "0.0.0.0"
                ParaCortar.append (str(nombre) + ';' + str(deuda) + ';' + str(corte) + ';' + correo + "\n")
                
            if deuda == 0:
                nodeudores += 1    
                #print (Fore.GREEN + "> El usuario", limp2[x]["nombre"], "NO debe la boletas")
                nombre = limp2[x]["nombre"]
                analisis = analisis + Fore.GREEN + ("> El usuario " + nombre + " NO debe facturas" "\n")
    
def enviarcorreo():
    global ParaCortar, enviados

    now = datetime.datetime.now()
    if now.strftime("%d/%m/%Y") == ("12/11/2022"):
        if now.strftime("%H:%M") >= "18:00":
            if enviados:
                for m in ParaCortar:
                    try:
                        print("ENVIANDO MAILS RECORDATORIOS...")
                        nombre = m.split(";")[0].replace("\n", "").replace("_", " ")
                        monto = "$" + m.split(";")[1].replace("\n", "")
                        mail = m.split(";")[3].replace("\n", "")
                        enviarmail(mail, monto, nombre)
                        print ("Correo enviado a:", nombre)
                    except:
                        print ("error al enviar mail en", m)
                enviados = 0

def limpiar():
    global analisis, total, deudores, nodeudores, ParaCortar
    analisis = ""
    total = 0
    deudores = 0
    nodeudores = 0
    ParaCortar = []
def comenzar():
    while True:
        time.sleep(5)
        pedir() #actualiza lista de cortes
        enviarcorreo()
        now = datetime.datetime.now()
        if now.strftime("%d") == ("15"): #si el dia actual es el dia programado procede los cortes
            #print(now.strftime("%H:%M"))
            if now.strftime("%H:%M") >= "08:00":
                print("CORTANDO...")
                revisar(1) #AQUI HACEMOS CORTES

        print("revisando...")
        pedir()
        revisar (0) #RESTAURACION DE CONEXION
def guardarcorte():
    global ParaCortar
    with open('corte.txt', 'w', encoding='utf-8') as file:
                
        for i in ParaCortar:
            file.write(i)

        file.close()

def revisar(corteok):
    global ParaCortar, cortados
    cortados = []
    reconectar = []
    guardo = 0
    c = open('cortados.txt', 'r', encoding='utf-8')
    cortados = (c.readlines())
    if len(cortados) > 1:
        for e in cortados:
            B = 0
            for id, a in enumerate (ParaCortar):
                if a.split(";")[2].replace("\n", "") == e.split(";")[2].replace("\n", ""):
                    ParaCortar.pop (id)
                    B += 1
            if B == 0:
                reconectar.append (e)
        
        for Reco in reconectar:
            guardo = coneccion(Reco, 1)
        
        if guardo == 1:
            for e in reconectar:
                
                for id, a in enumerate (cortados):
                    if a.split(";")[2].replace("\n", "") == e.split(";")[2].replace("\n", ""):
                        cortados.pop (id)
                        
            GuardarCortados(cortados)    

        for s2 in reconectar:
            for id3, s in enumerate(cortados):
                if s.split(";")[2].replace("\n", "") == s2.split(";")[2].replace("\n", ""):
                    cortados.pop(id3)
        
    if corteok:
        for plan in ParaCortar: #bucle lista corte
            coneccion(plan, 0)
            GuardarCortados (cortados)
        
def coneccion(H, funcion):
    global cortados
    USER = 'admin'
    PASSWORD = ''
    HOST = H.split(";")[2].replace("\n", "")
    print (Fore.YELLOW + "█ Conectando a: " + HOST, H.split(";")[0].replace("\n", ""))
    
    client = pm.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(pm.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=5)
    except:
        print(Fore.RED + " - X ERROR AL CONECTAR CON",HOST)
        now = datetime.datetime.now()
        elerror = now.strftime("%d/%m/%Y"), " - ", now.strftime("%H:%M"), " - X ERROR AL CONECTAR CON ", HOST, "\n"
        guardarerror(elerror)
        return
    print (Fore.GREEN + "█ Conectado")
    channel = client.invoke_shell()
    RESULTS = channel.recv(8192)
    print(RESULTS)
    if funcion == 0:
        channel.send('config set wirelessMIRSTAProfileNumber 1' + '\n') #REDUCIR PLAN DESDE ANTENA CLIENTE
    
    if funcion == 1:
        channel.send('config set wirelessMIRSTAProfileNumber 0' + '\n') #PLAN NORMAL
    time.sleep (1)
    channel.send('config save\n')
    time.sleep (1)
    channel.send('config apply\n')
    if funcion == 1:
        return 1
    if funcion == 0:
        cortados.append (H)
def GuardarCortados(hosts):
    with open('cortados.txt', 'w', encoding='utf-8') as file:
                
        for i in hosts:
            file.write(i)
        file.close()

def guardarerror(hosts):
    with open('error.txt', 'a', encoding='utf-8') as file:
                
        for i in hosts:
            file.write(i)
        file.close()

enviados = 1
analisis = ""
total = 0
deudores = 0
nodeudores = 0
ParaCortar = []
url1 = "http://futurnet.nullinformatica.com.ar/api/3/clientes?limit=50&offset="
headers = {
'Token': ''
}

if __name__ =="__main__":

    comenzar()

