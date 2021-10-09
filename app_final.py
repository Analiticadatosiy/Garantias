import streamlit             as st
import seaborn               as sns
import plotly.express        as px
import pandas                as pd
import numpy                 as np
import plotly.figure_factory as ff
import matplotlib.pyplot     as plt
import pydeck                as pdk
from datetime import datetime, timedelta
from PIL import Image 
import base64
import re

st.set_option('deprecation.showPyplotGlobalUse', False)	

st.set_page_config(
	layout="wide",  # Can be "centered" or "wide". In the future also "dashboard", etc.
	initial_sidebar_state="auto",  # Can be "auto", "expanded", "collapsed"
	page_title='Garantías',  # String or None. Strings get appended with "• Streamlit". 
	page_icon=None,  # String, anything supported by st.image, or None.
)

st.title("Repuestos Garantías")

# Cargamos el archivo
df = pd.read_csv('PredGarantias0701.csv', sep=";" ,encoding= 'unicode_escape')
#df.drop(['Unnamed: 0'],axis=1, inplace=True)

# para borrar tildes y reemplazar espacios con _
clean_accent=(lambda x: x.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8'))
df.columns=clean_accent(df.columns)
df.columns = df.columns.str.replace(' ', '_')
st.write(df.columns)
# establecer el formato fechas
df['Fecha_documento'] = pd.to_datetime(df['Fecha_documento'])
df['Fecha_dictamen_tecnico'] = pd.to_datetime(df['Fecha_dictamen_tecnico'])
df['Fecha_compra_lote_CBU'] = pd.to_datetime(df['Fecha_compra_lote_CBU'])
df['Fecha_produccion_CKD'] = pd.to_datetime(df['Fecha_produccion_CKD'])
df['Fecha_Venta_Distribuidor'] = pd.to_datetime(df['Fecha_Venta_Distribuidor'])
df['Fecha_venta_cliente_final'] = pd.to_datetime(df['Fecha_venta_cliente_final'])
df['Fecha_envio'] = pd.to_datetime(df['Fecha_envio'])

# quito las columnas que en este punto del estudio no agregan mucha informacion
df.drop(['Reclamo', 'Verificado','Fecha_documento','Mes_dictamen','Lote_CBU', 'Fecha_compra_lote_CBU','Lote_CKD', 'Fecha_produccion_CKD',
         'Orden_produccion','Tempario','Descripcion_tempario', 'Tiempo_tempario', 'Pais','Distribuidor','Nombre_distribuidor_reclamacion',
         'Tienda','Centro_de_responsabilidad_venta', 'Distribuidor_venta','Nombre_distribuidor_venta', 'Tienda_venta', 'Ciudad'],axis=1, inplace=True)

# Filtro sólo negocio motocicletas
df_MC=df[df['Codigo_Negocio']==1000]

# Elimino registros de PSER sospechoso
df_MC=df_MC[df_MC['Numero_solicitud']!='PSER_650041']

# Solo tenemos en cuenta los productos
df_MC=df_MC[df_MC['Tipo_producto']=='Producto']

# No tenemos en cuenta los productos que se hacen en campaña
df_MC=df_MC[df_MC['Codigo_sintoma']!='ZZ']

# No tenemos en cuenta los productos que se hacen en campaña
df_MC=df_MC[df_MC['Condicion']!='ZZ']

# Elimino columnas innecesarias
df_MC.reset_index(inplace=True)
#df_MC.drop(['index','Nombre_Comercial','Fecha_venta_distribuidor','Proveedor_orden_compra','Pais_proveedor', 'Codigo_Negocio'],axis=1, inplace=True)

#Para quedarme con las variables que me interesan y en el orden que me interesa
df_MC=df_MC[['Numero_solicitud', 'Kilometraje_falla', 'Fecha_dictamen_tecnico','Numero_de_motor','Clasificacion_MC','Categoria',
             'NombreComercial','Nombre_GrupoClasificacion', 'Codigo_modelo_1', 'Codigo_modelo_2','Descripcion_modelo',
             'Color','Proveedor_Origen_Compra','Pais_Origen','Fecha_Venta_Distribuidor','Fecha_venta_cliente_final','Tipo_producto',
             'Dimension_Producto_Repuesto','Categoria_Producto_Repuesto','Item_Grupo_Descuento_Producto','Categoria_Japon_Producto',
             'Proveedor','Producto', 'Descripcion_producto','Cantidad', 'PFP', 'PFP_asociado', 'Descripcion_PFP', 'Codigo_sintoma',
             'Descripcion_codigo_sintoma', 'Condicion', 'Descripcion_condicion','Fecha_envio','Lead_Time_Calculation',
             'Centro_de_responsabilidad_reclamacion','Ciudad_reclamacion']]

# Organizando proveedores:
# Agrupando MBK y TYM porque hay muy pocos registros y porque de esos origenes ya no llega nada
df_MC['Proveedor_Origen_Compra']= df_MC['Proveedor_Origen_Compra'].apply(lambda x: x if x not in (['MBKCOM','TYM']) else 'OTROS')
df_MC['Pais_Origen']= df_MC['Pais_Origen'].apply(lambda x: x if x not in (['FRANCE','THAILAND']) else 'OTROS')

# Agrupando los no declarados con japon, porque los revisamos con santiago alvarez y dijo que eran japon
df_MC['Proveedor_Origen_Compra']= df_MC['Proveedor_Origen_Compra'].apply(lambda x: x if x!='NO DECLARADOS (VARIOS)' else 'YMC')
df_MC['Pais_Origen']= df_MC['Pais_Origen'].apply(lambda x: x if x!='NO DECLARADOS (VARIOS)' else 'JAPON')

# Agrupando los estados unidos con OTROS
df_MC['Proveedor_Origen_Compra']= df_MC['Proveedor_Origen_Compra'].apply(lambda x: x if x!='UNITED STATES' else 'OTROS')
df_MC['Pais_Origen']= df_MC['Pais_Origen'].apply(lambda x: x if x!='UNITED STATES' else 'OTROS')

# Creando otras variables de tiempo
df_MC['AñoMes_dictamen'] = df_MC['Fecha_dictamen_tecnico'].map(lambda date: 100*date.year + date.month)
df_MC['Mes_dictamen'] = df_MC['Fecha_dictamen_tecnico'].dt.month

# Calculo del tiempo para el envio del repuesto (resta entre la fecha envio y la fecha dictamen tecnico)
df_MC['tiempo_atencion'] = (df_MC['Fecha_envio'] - df_MC['Fecha_dictamen_tecnico'])
df_MC['tiempo_atencion'] = df_MC['tiempo_atencion'].apply(lambda x: x.days)

# Calculo del tiempo que llevaba la moto de ser vendida a cliente final:
df_MC['tiempo_venta']= (df_MC['Fecha_dictamen_tecnico'] - df_MC['Fecha_venta_cliente_final'])
df_MC['tiempo_venta'] = df_MC['tiempo_venta'].apply(lambda x: x.days)

# Calculo del tiempo que llevaba la moto de ser vendida a cliente final:
df_MC['tiempo_exhib']= (df_MC['Fecha_venta_cliente_final'] - df_MC['Fecha_Venta_Distribuidor'])
df_MC['tiempo_exhib'] = df_MC['tiempo_exhib'].apply(lambda x: x.days)

dataset=df_MC.copy()

def conteo_alpha(x):
  cuenta=0
  for i in range(0,len(x),1):
    if x[i].isalpha():
        cuenta += 1
  return cuenta 

def reemplazo_origenes(x):
  if x[0]=='E':
    x=x.replace(x[0], '1')
  if x[0]=='F':
    x=x.replace(x[0], '2')
  if x[0]=='H':
    x=x.replace(x[0], '8')
  return x 

dataset['Key_Producto']=dataset['Producto'].apply(lambda x: x[0:5] if x[0]=='9' else x[3:8])
dataset['Conteo_letras']=dataset['Key_Producto'].apply(lambda x: conteo_alpha(x))
dataset['Key_definitivo']=dataset['Key_Producto'].apply(lambda x: reemplazo_origenes(x) if conteo_alpha(x)==1 else x)

# Para quitar los caracteres especiales pero consevar los guiones y los slash
dataset['Descripcion_producto_procesada'] = dataset.Descripcion_producto.apply(lambda x: re.sub(r"[^a-z\-\/A-Z\-\/0-9\-\/]"," ",str(x))) 

abreviaturas={'AIR':'AIRE','AMAR':'AMARILLO','CADENI':'CADENILLA','CAL':'CALCOMANIA','CALC':'CALCOMANIA','CALCA':'CALCOMANIA',
              'CALCCUBTANQ':'CALCOMANIA CUBIERTA TANQUE','CALCCUBTANQSUPIZQNEG':'CALCOMANIA CUBIERTA TANQUE SUPERIOR IZQUIERDA',
              'CARCA|ZA':'CARCAZA','COMP':'COMPLETO','COMPL':'COMPLETO','CONDUCT':'CONDUCTOR','CRAN':'CRANK',
              'CRANCK':'CRANK','CTA':'CUBIERTA','CUB':'CUBIERTA','CUBTAN':'CUBIERTA TANQUE','CUBTANSUP':'CUBIERTA TANQUE SUPERIOR',
              'DEL':'DELANTERO','DEL/TRA':'DELANTERO/TRASERO','DER':'DERECHO','DESCOMPRESSION':'DESCOMPRESION','DIRECC':'DIRECCION',
              'FREN':'FRENO','FRO':'FRONTAL','FRON':'FRONTAL','G/FANGO':'GUARDAFANGO','IMPUL':'IMPULSO','INF':'INFERIOR',
              'INFDER':'INFERIOR DERECHA','INFIZQ':'INFERIOR IZQUIERDA','IZ':'IZQUIERDO','IZQ':'IZQUIERDO','JGO':'JUEGO',
              'LAT':'LATERAL','LAT.':'LATERAL','MANZAN':'MANZANA','PANELFRO':'PANEL FRONTAL','PANELFRON':'PANEL FRONTAL',
              'PANELINF':'PANEL INFERIOR','PANELSUP':'PANEL SUPERIOR','PANFRON':'PANEL FRONTAL','PAS':'PASAJERO',
              'RECUPERA':'RECUPERACION','REPOS':'REPOSAPIES','RIM':'RIN','SOP':'SOPORTE','SOPOR':'SOPORTE','SPROK':'SPROKET',
              'STD':'ESTANDAR','SUICHE':'SUICHE','SUITCHE':'SUICHE','SUP':'SUPERIOR','SWITCH':'SUICHE','TANQ':'TANQUE',
              'TANQINF':'TANQUE INFERIOR','TANQSUP':'TANQUE SUPERIOR','TAPA 155':'TAPA','TAPALAT':'TAPA LATERAL','TRACC':'TRACCION',
              'TRANSM':'TRANSMISIÓN','TRAS':'TRASERO', 'SUSP':'SUSPENSION','SUSPENSI':'SUSPENSION','DIREC':'DIRECCION','DIST':'DISTRIBUCION',
              'O RING':'ORING','CARBURAD':'CARBURADOR','O-RING':'ORING','CLUTH':'CLUTCH', 'TRANSMISI':'TRANSMISION', 'PASAJ':'PASAJERO',
              'CIGUE':'CIGUENAL','CIGUEN':'CIGUENAL','Del':'DELANTERO','Llanta':'LLANTA','PISTONYBR125E':'PISTON YBR125E','TENSORYBR125E1BV1':'TENSOR YBR125E 1BV1',
              'CRNAK':'CRANK','WHEELYBR125E':'WHEEL YBR125E','RUED':'RUEDA','PISTO':'PISTON','TENSORYBR125E1BV1':'TENSOR YBR125E 1BV1','COM':'COMPLETO',
              'AMORT':'AMORTIGUADOR','COMPLET':'COMPLETO','CILINDRO1':'CILINDRO 1','VAL':'VALVULA','VALV':'VALVULA','ADMIS':'ADMISION','VALVE':'VALVULA',
              'ESPCAPE':'ESCAPE','VALVYBR125E':'VALV YBR125E','CADENILL':'CADENILLA','CAD':'CADENILLA','ACEI':'ACEITE','FILTR':'FILTRO','ACEIT':'ACEITE','ABRAZ':'ABRAZADERA',
              'CARBURADOR4B41/51YW125':'CARBURADOR 4B41/51YW125','GASOLINA4B41/51':'GASOLINA 4B41/51','LUBRICAC':'LUBRICACION','CARBUR':'CARBURADOR','ACEITYBR125E':'ACEITE YBR125E',
              'DER4B41/51YW125':'DERECHO 4B41/51YW125','DERECHAYZFR15':'DERECHO YZFR15','MANZ':'MANZANA','CLUTYBR125E':'CLUTCH YBR125E','CLUTCHFZ16':'CLUTCH FZ16',
              'CLUTCHFZ16/R1511':'CLUTCH FZ16/R1511','EMBR':'EMBRAGUE','COMPLET':'COMPLETO','PRESIONT115':'PRESION T115','3ta':'3RA','3DA':'3RA','SAL':'SALIDA','POLE':'POLEA',
              'SECUNDARIAYW125':'SECUNDARIA YW125','SECU':'SECUNDARIO','CAMBIOSYBR125E':'CAMBIOS YBR125E','SELEC':'SELECTOR',' IZQT115':'IZQUIERDO T115','CAMBIO1':'CAMBIOS 1',
              'AMORTI':'AMORTIGUADOR','TIJER':'TIJERA','AJUS':'AJUSTE','COMPYZF-R3':'COMPLETO YZF-R3','INFER':'INFERIOR','SUSPEN':'SUSPENSION','HORQU':'HORQUILLA','SUPIZQ':'SUPERIOR IZQUIERDO',
              'SUPDER':'SUPERIOR DERECHO','AIRSUP':'AIRE SUPERIOR','CTATANQ':'CUBIERTA TANQUE','GASYBR125E':'GAS YBR125E','COLAYBR125E1BV':'COLA YBR125E 1BV','COMBU':'COMBUSTIBLE',
              'DELANTER':'DELANTERO','TR':'TRASERO','TRA':'TRASERO','TAP':'TAPA','CARB':'CARBURADOR','TORNI':'TORNILLO','FRE':'FRENO','DISC':'DISCO','MAES':'MAESTRO','MAESTR':'MAESTRO',
              'COMPLE':'COMPLETO','DIR':'DIRECCION','ARRAN':'ARRANQUE','INTE':'INTERNO','MANUBRIO1BN11BN2':'MANUBRIO 1BN1 1BN2','RIGHT':'DERECHO','PORTACASCBA51':'PORTACASCO BA51',
              'TANQU':'TANQUE','GA':'GAS','DEL/TRAS':'DELANTERO/TRASERO','FAROLAYW125FI':'FAROLA YW125FI','FITRO':'FILTRO','DRENAJ':'DRENAJE','TANQUEGASOL':'TANQUE GASOLINA',
              'ACEIE':'ACEITE','TORN':'TORNILLO','CAMB':'CAMBIO','INYECT':'INYECTOR','VELOC':'VELOCIMETRO','DELR15':'DELANTERO R15','CARC':'CARCAZA','DISTRIBUCCION':'DISTRIBUCION',
              'DISTR':'DISTRIBUCION','DISTRIBUCI':'DISTRIBUCION','DIS':'DISTRIBUCION','Tras':'TRASERO','140/60-17FZ16':'140/60-17 FZ16','BOMB':'BOMBA','TRANS':'TRANSMISION','CLUT':'CLUTCH',
              'ARRAN':'ARRANQUE','ACE':'ACEITE','TAP':'TAPA','RADIA':'RADIADOR','MAES':'MAESTRO','FRENONMAX':'FRENO NMAX','CARCAZAX-MAX300':'CARCAZA X-MAX300','TRANSMISI':'TRANSMISION',
              'VALT115':'VALVULA T115','VALVYBR125E':'VALVULA YBR125E','VAULVULA':'VALVULA','CADENILLA2':'CADENILLA','COMPLETOXSR900':'COMPLETO XSR900','VENTILAD':'VENTILADOR','EMPAQ':'EMPAQUE',
              'VALVSOLENOIDE':'VALVULA SOLENOIDE','AGU':'AGUJA','CARBU':'CARBURADOR','CARBURADORYBR125E':'CARBURADOR YBR125E','AJUST':'AJUSTE','PULVERIZADORYFM90':'PULVERIZADOR YFM90',
              'AIREYFM90':'AIRE YFM90','CARBURADORYFM90':'CARBURADOR YFM90','ESC':'ESCAPE','MOFL':'MOFLE','MOFLE4B41/51YW125':'MOFLE 4B41/51YW125','RESONAN':'RESONADOR','FILT':'FILTRO',
              'INDUCC':'INDUCCION','CULATA/YW125':'CULATA YW125','CARZ':'CARCAZA','DRCHO':'DERECHO','CARCA':'CARCAZA','AUTOMATIC':'AUTOMATICO','ARRA':'ARRANQUE','ARRAT115FSE':'ARRANQUE T115FSE',
              'TRANSMISI':'TRANSMISION','PRES':'PRESION','DELYZF-R15':'DELANTERO YZF-R15','DELAN':'DELANTERO','MOT':'MOTOR','RECUP':'RECUPERACION','COMPLETT115BF21':'COMPLETA T115 BF21',
              'COMPLETAYW125DX':'COMPLETA YW125DX','XZT125':'XTZ125','SUSPENS':'SUSPENSION', 'COMLETA':'COMPLETA'}

def reemplazo_palabras(x,abreviaturas):
  palabras = str(x).split()
  texto = [abreviaturas[palabra] if palabra in abreviaturas else palabra for palabra in palabras]
  cambio = " ".join(texto)
  return cambio 

dataset.Descripcion_producto_procesada=dataset.Descripcion_producto_procesada.apply(lambda x: reemplazo_palabras(x,abreviaturas))

# Diccionario palabras a eliminar (colores, marcas, nombres modelos)
eliminar = ['FZS1000/2007','YZFR3','NMAX','MT03','TRICY','XTZ150','XT660','YW125','MAXX','MAXXI','MAXXIS','FZ15','T115','T115FI',
                    'FI','BF21','(BF21)','ROJA','NEGRA','AZUL','BF24','ED.','ESPECIAL', 'GO','AMARILLA','GRIS','RACING', 'SPIRIT','NEGR','ARENA','HYPERLIGH',
                    'CHAMPAGNE','BLANCA','BBL1','BA4','BA45','BA44','B735','B731','B728','B727','BU61','B6U1','B393','B1L1','B0A1','2MD6',
                    '2MD5','2MD4','RED','2DU4','1BV3','SILVER','YW125X','FAZER15','SZRR','YZF-R15','YC110D','XTZ125','XTZ','YD125','ONE',
                    'SPIRIT','EDI.','CIAN','N','DUAL','THUNDER','VERDE','ARROW','EDI. ESPECIAL','RACING','MATE','10TH','YZF-R1','RINHO',
                    'RACE BLU','FZSFI','FZ','SZ','N-MAX','GPD150-A','BC21','GPD150-A(NMAX)','MTN850-A','YZ450F','YZF-R3','2MS1','YZFR15 V3',
                    'NEXT/RXS/DT200','XT225/RXS/NEXT','NEGRO','YZF600','YZF-R6','YZFR6','YZFR15','BK31','BK3','NEGRO MATE','M/C','ED RACE BLU',
                    'ED. RACE BLU','DORADO','BC24','BA41','BF2','RB','AZU','T115 FI','N-R','N-A','AMARILLO','CRYPTON','SZ-16','(BDG)',
                    'BDG','MT09','YFM90R','XTZ250','BC2','BBL','FZ-16','YW125FI','BA5','YW125 FI','4B41/51YW125','BWSFI','NEG','BWS',
                    'HILO AZUL','BWS X','BWSX','BA51','CHMP','X125','BWSXFI','HYPERLIG','BA4/5','HYPERLIGHT','4B41/51','YW12','B9L',
                    'B9L1','FZN250','FZN250-A','B8V2','GRISMAT','B72','ED. ESP.','BLUE CORE','NEGMAT','B722','MAT','RAC.SPIRIT','R.SPIRIT',
                    'BLANCO','B728/B735','B6U','BCA','RX/T110/NEXT/2BN1','T110/RXS/RX115','MTN1000','MT10','X-MAX300','B74K','GPD150A',
                    'GPD150','MTT850','(MT09TRA)','MT07','YZF-R15/FZ-16','/SZ-RR','SZ15RR','B39','B391/','ED. RACE BLUE','ED RACE BLUE',
                    'FZ-16','FZ250','YFM700','FZ16/R1','YTZ5S','DUNLOP','FZN150','V80/T110/YBR','SZ16','5P42','FZ16','LIB','FZ16','FZ15S',
                    'FZN150','FAZER-15/FZ-15','YZFR1/FZ-16','5P42','SR150/XT225','YBR125E','YW125/09','XTZ 150','YW100/YW125','BA51/53','45D3',
                    'YBR125/XTZ125','2YBR125E', '1BV1', '2YBR125E','N-MAX/YZFR15 V3','N-MAX','YZFR15 V3','XT660R','1YBR125E','1BV1','1YBR125',
                    'XTZ125','1YBR125E','YBR250/XTZ250','YBR250','XTZ250','5C91','XT660E/XT660R','MARRON','YZF-R1/XTZ250','YBR125/5P42','YBR250','YBR125',
                    'YFM', '250/XTZ250','YS250','YFM250/XTZ250','XT200/XT225/FZ25','XT200/XT225','XT225/YBR250','T110E','XT200/225/XT660R','FZ1/R1/R6',
                    'XT660R/XT225','YBR125/XTZ12','MT07','XT200', 'XT225/99','XV250/T110E/XTZ125','YBR250','XT200/XT22599','B721','NEXT','XT200/','YZ250N',
                    'MT09TR','T112','XT600/97/XT660R','XV250','MT-09 TRA','YFZ450T','YFM660','YBR125/YBR125SS','XT1200Z','XT250/500/600/YF','1ED8',
                    'YFM700R','MT-09','XVS950A','XT660Z','3S81/5P42','T110-LIBERO','T110','LIBERO','YBR250/YZF-R15','TTR-50','T110E','YBR250/YZF-R15',
                    '3S81 NEXT','5P4 FZ-16/57C1','FZ-16/57C1','YW100','T110E/XV250/5P42','XV535','5C91','VMX1200','XT1200','XT500/XTZ250','XT350K/660R/250',
                    'YFZR1/05','XV250/XTZ125','FZS10V','LIBERO 5C91','YFM660','YBR250/XTZ250','YBR250/XTZ','24T', 'YBR250/XTZ25','VIRAGO', '/XT660R','YZF450/XT660R',
                    'MTM850','T110E','T110 00','T110-00','1WD1','1SB3','58P4','24P','58P4', 'MP','XT1200','YZFR15/FZ-16','XT500/XTZ250','5C91/5C92',
                    '2BN12BN2','2BN1','2BN2','V3','EU3','1SB3','2CD1','1SB3/5/8','B0A//YC110D', 'AMORTIZ','2MD', 'EU3','Euro 3','20D3',
                    '/XTZ125','XV250/XTZ125','XT350K/660R/250','YFZR1/05','20D3','YZFR15/FZ16','XT660R/07','/YW125','No 102','YZ2502002/YW125','XMAX',
                    'FZ-16ST1EP2/3/4/5','1 NW125','4B41/51YW125','FZS10V','B841','TRICITY','1TRICITY','5C91/5C92/5P42','YFM660','T115FS','YBR125E1BV1',
                    'YBR250/XTZ','T115FSE','YBR125','YBR125E1BV1','1SB3','XTZ1251SB3','YW125DX','R15B42','R15B42','MTN320-A','/FAZER-15/FZ-15','1EP2/3/4/5',
                    '45D1', '45D1','45D2','B391','FZ16/DT125','XTZ125E','5P42/FZ16','YBR125/FZ16','BA41/51','YW125DX','/FZ16','45D6 GP','BB5L-B-SLA','EDI ESPECIAL',
                    'N-MAX/F2N150D/6F2N150D/6F2H150/GPD1','T115FSE','6F2N150D','F2N150D','6F2H150','GPD1','T115FSE','YZF-R15/2019','4B41/51YW1','FZ-15','BA41/51',
                    'YBR125ESD','YZF', 'R15','B391','YBR/FZ16','V3','2MD3','YZF-RM1','1BN11BN2','YFZR15','4B41/51YW12','XTZ125E','YW125DX','1WD1','SZ16B391','/XTZ125',
                    '/YW125X', '2DU3','428-98LL','XTZ250Z','5C9/FZ-16','FZ-15','BF21/22','5P42/5C92/FZ16','RX100/5C91/5C92','5P42/RX100','BA41/51','YW1252017','S PINT',
                    'T115FSE','Dunlop','391','N-MAX/YZFR15','YCZ','YFZ R15','YFZ','R15','YW125/08','3B22','3B23','XTZ250X','R15','1ED9','3C11','YZFR1','FZH150',
                    'SX-4','DT125/175/200','YZF','YFM', '250/XTZ250','3S81','5C9/FZ16','XT660R/2007','N-MAX/F2N150D/6F2N150D/6F2H150/GPD1','FZN150D-6','B6U2','YBR/XTZ125/NEXT/FZ16',
                    'FZ16/YBR','58P3','BA41/5','YBR/XTZ125/NEXT/FZ16','DT125/RX115','DT200', 'YBR125E','XT225','DT125/XT660R/1BV','XV250/YW125','LIBERO125','YBR250/',
                    'R1','/XTZ250','YA90/CY50/YW100','1BV1SIN','P','LIBERO125','LIB125','VERD','LIB125','1BV125','BA41/5','T115F','2MD2','SIN','S','PIN','PINT','XT350K/XT225','XV250/535',
                    'TTR50','YBR/XTZ125/NEXT/FZ16','YBR125SS','TTR50','SZ-16R','2MD5/2MD6','B6U2','FZ-16/YZFR15','2011','DT125/XT660R/1BV','DT125/RX115','YBR/XTZ125/NEXT/FZ16',
                    'X225/XV250/YBR125','FZ6-6','XT200/25','XT350K/XT225','YBR125SS','XTZ250/YBR250','B8V1','WR200/XT600','R15/T115/YBR250','XT225/XTZ250/YBR2','DR8EA','XT500/YW125/09',
                    'FZ-161EP1/7','YBR251BV1/2/3','XTZ12','3S81/XTZ250','VOLT110/XT200/XT600','XT600','99','YBR250/XTZ2','2','3','1','BF212016','T115BF21/22','/MT07','TTR5','SZ16R',
                    '/YZF-R15','B281','SZR','T115BF21','YBR','FINOB281','XT600R','45D5/6','liber','5C9/5P42/FZ-16','YMF660','YZF-R25','4B41/51YW125','3C14','MT','09','150','4B41/51',
                    'R15B121','T115BF21','B281','5P4','YBR125ESD2013/14','Euro','AMORTZ','NW125','4B41/51YW125','YZFR15','1SV1/2','R15/11','FZ16/R1511','FZ-16/YZF1R5','FZ-16/R15/11',
                    'FZ-16/R15/11','FZ25','R-15','XT250Z','-16','FZ-16/R15','00','T115','YS250/XTZ250','125E','2MD4/5','1BV','LIBERO/5P42','AL125FX','45D6/1EP5','ENSAM','B0A','1BN2',
                    '/YD125','1BN2','PINTAR','PINTAR','SZ16-R','XTZ126','XTZ125/XTZ250','2MD2/3','2017','SZ-R','1BN1','VRC1','VRC1','FZ-16ST','YZF-R25','TENE','2020','XTZ150-2','RXS115/RX100/T110',
                    'DT125/200','RXS115/00','XT600/XT660R','97/XT660R','DORAD','ROJO','WH','45D6','YZF-R3','CY50/98','DORADOYW125X','PN006565-YP','XT1200ZE','XT250/SR250',
                    '99/FZ-16','YFZR1/FZ16','57C1','1B1V','LIBER125','/','RX115S/YBR125','YZ125','T110E/T115','SZ16-B391','2013','B281/T115','B281','FINO','5C9/5P42/FZ-16','YBR1251BV',
                    'DT125/175','LIBERO/5P42','XJ600','XTZ150-2','1SV1','15','ALL', 'BLA','PRO','RAC','BLANC','BLAN','AZUL2MD4','AZRT','1BV','V80/T110','ED','ESP','YCZ110','X','THERMOLINER',
                    'RACE','BLU','MQ','45D-1SV2','125','660','XT', 'Z','2DU1','TTR-50E','45D','DT125/175','GRSI','BRILLANTE','V80/T110/RXS115/','DT125/175/XV250/T11','57C1/FZ-16','METALICO',
                    'METALICO','MT09TRA','CROMAD','5','4','PURP','R15B842','4B41/51YW125FI','DT125/XT200','NEGRO/AZUL','AJUSYBR125E1BV1TTR5','YZF-R1/04-05', 'YTZ10S','GP','EDI',
                    'NEGR-AZUL','YW25/09','R15/SZ16','2MD4/2MD5/2MD6','1BV1/TTR50','115','B395','1BN8','155','FZN251','SZ/R','PINTA','NEG/ROJA','XT66020D3','EURO','YW100/01','XT660R/2008','R3',
                    'DT200/DT125/175/22','1MT-09','DT125/','3S1','32B1','FZS1000','XV535/FZ-16','RX100/115/T110/FZ-16','YZF-R6/R1 FZ-6','XTZ250/125','YD110/T115','YA90/YW100','YBR250/NEXT',
                    'FZ16/FZ15/SZ16','V80/RX100','DT125K','RX100','YW100/YD110/XT225','V80','RX115S/YZ400/YW125/09','RX115/YW125','YW100/DT/FZ16','DT125K','FZ16/NEXT/YA90','VMAX1200','DT125/V80/1BV1',
                    'DT200/97','YW125/FZ-16','T110E/RXS115/R15/FZ16','RX100','DT125','RX115/XT60/YW125/R15','XT225/FZ-16','YW100/01/YZF-R15/FZ-16','NEXT/FZ-16','3S8','FZR400','5C9/T110',
                    'RX115/V80/XTZ250','YW100/YZF-R15','KR','T110E/YW125/09/YZF-R15','YW100/XT660R/FZ','XTZ125/FZ-16','RX100/FZ16','RX115/YZF-R3','DT125K/FZ-16','YW100/5C9/FZ-16','XT600/XT660R/FZ-16',
                    'YXR450F','YZ250','XVS1300','XV250/YBR250/T115','CR6HSA','CR7E','NGK-CPR8EA-9','CR6HS','XV250/YBR125','XT225/XT250/YBR2','D8EA','XT200/XT350/YFM35','CR8E','DID520VP2', '110LE',
                    'DID525V10-110LL','YFM700G/YXR700F','DID428VIX3','128LE','1ED1/1ED9','520-112','DID','DT15/175/XTZ','DT125/200/XT35','RX100/115/YBR','DT125/XT600','DT125','MT70','LIB/YBR',
                    'ME22','ME','XTZ2','Pirelli','PIRELLI','MICHELIN','MT60/XTZ150-2','5C9/5P42/FZ16','XTZ250/XT225','NACHI','YZ250','RX115','RXS','RX100A/5P42/LIBERO','YBR250/R3','YZ80',
                    'YFB250','YZ125/YZ400','YZ400','FZ8','YBR250/XTZ/R15','02/XT660R','KOYO','2P61/FZ16','CY/YA90/YW100','V80/YBR125','2P61','YFM350/YZ85/MJ50','RX115','T110/RX',' XT660/YW125','RXS115',
                    'AL115F','YFM400','XT225/350/60','XT225/06','XT225/YZFR15','XT350K','YZFR-15','DT200/YZ4','XV250/06','CY50/YA90','2BN','V100E','FZ-1','SR150/XT225/99','XT500','XT660/XTZ2','2P61',
                    'YBR126/XTZ12','SR150','RX115','XT225/','XT600/99','SR150/XT225/XT600/FZ16','XT225/YFM450','XT250','YZ250F','YFM350','YBR250/FZ250','XT220/XT225/99','XJR1200','T110/XJ600','V80/DT','TZR250',
                    'XT225/350','YZ80/XT660R','YZ125/XT660R','DT/RX/XT225','YZ400','98/YBR125/XTZ2','MT03/YZFR3','BBE1','B7H1','YW125XFI','YB125ZR','AL115FX','YZF155-A','BEU1','FZ16ST','BWS125',
                    'DT/YBR/','DT125/175/RXS1','5C92','YZF-R15B841','DT175K','RXS/99','DT175','20D2','DT175EFGK','FZ6-S','RX115/RXS115','RX125/DT125K',' XT225/XT200','XT600E','YFM70R','1XB6',
                    '57C','/YZF-R1','V80/94','XT600E','YFM250','YFM7FGPW','YZF-R6R','WR450F','TDM80','2NEGRA','FZ1','T110ED','1XB06','5C92','YZ426/WR450F','T115FSEBF21','T110E/XV250','XT225/STD', 'YFB2',
                    'V80/FS80','T110ED','FZ8-N','XV250/T110','YZ450F/03','FZ6-S/2005','DT125K/175K','MARRO','58P1','P4','/XT660R/XT660X','03','FZ1-N','YFZ-R6','XV250/YBR125/XTZ1','YZ400/3S81','01/R1',
                    '2016','YBR125/3S81','YZF750SP','2PB12013','YZ250N/01','FZR-400','FZR400/YZFR6','YZ250N/01','FZR-400','WR250F','5VK', '20D1','R6','T110/XV250','XT225/350/YZ400','XT200/225','YZ400/98',
                    'XT200/225','1S71','FZ8-N','TDM850','YFM70R','/YZF-R6','/2006','2006','XSR900','XJ6N','1XB6','DT200/YZ80/XT22','WR400','FZ1000','YW125/0','RX115/RXS','XT200/XT225/SEROW',
                    'XT660X','XT225/XV250','1S71','TDM900','XT200/225/350','YZ450/XTZ250','YZFR1/R6/FZS100','5C91/5P42/5C92','5C91','5P42','5C92','XTZ660R','TENERE','MTM850-A','YXM700','YW125/YW125X','XC125',
                    'DT125/175K','YFA1G','DT175/200','XV1100','/YZ450F','YZ450F','LB80','5DT200','FZF-R6','D125R','XVS650A','DT200R','DT100K', 'DT175K','RX115/RXS9','YFM350A','DT100/RX115','FZX250','V110E/XJ600/FZ16',
                    'YZ125/2002','RXS115/RX115','YW100/YFM50S','YFM50S','5C91/2','YBR1','YBR125/XTZ1','YFM350/XT2','RX','DT','ATV','YFM660GW','T110/DT125','YFM660/FZ16','YBR12/FZ1','XV535/5P42','VX750','YBR125/XTZ1',
                    'YBR125E1BV','YFM90','T105E','100YFM90','XT600/97','BR125E','DT125/92','YFM660GW','/YFM660G','YFM660G','DT100/125/175','/YZF-R6','YZF-R6','WR250R','5C92','YB125ZR','B7H1','YZFR6R/08','DT100/125/175K/95',
                    'FZ6-N','RX100/115/125','TDM900','WR450FT','XT600/00-03','XVS400','XVS950','YFM700FWAD','YFS200','2002-2005','YZF-R1/07','/YFM350G','YFM350G','DT125/92','YFM125S','V80/XT600/','DT175','XT500/YBR125',
                    'DT175','RX100/115/RXS115','DT125/175/TZR125','XT225/250','XV250/YFM50S/T11','YBR125/XT350','45D5','4B41/51YW125','MT07A','DT100/125','RX100/115/RXS','XT225/YFM350','45D5FZ16','Midnigth','DT125/17',
                    'YBR/08','YW125/','YW125','DT175E','YFM660GW','YFM350/XT225','RX115/RXS115','CAR','XTZ125/2MD6','YFM450','XT250/XV250','B2N2','02/YW125','YZ250/02','YZ80/2002', 'YZ250/2002','2BNFINO','3S81/5P42/32B1','YFM660R',
                    'YTZ14S','RX115/RXS','V80/DT100K','XV535A','MT-07','MT09A','YW125/YW125X','RX115/RXS','RX115/RXS-99','RX115/135','XT600E/97','XV535A','YFM125S','YFM125S','YZF-15','R1/FZ1/FZ8','/XJ6-F/XJ6-N','XJ6-F/XJ6-N',
                    '/XT1200Z','XT1200Z','FINB281','YZF-R15/2010','R6','WR450F/08','YFM70R','TDM9','XT600E/XT660R','/YZF-R1','YZF-R1','YFM350/400','YZFR','R-1','RX115/125/','RX115/125','DT100K/125/17','RX100/115/125',
                    'YZ65','YBR/XTZ125','45D5','5TL7','MT-03','YFZ450R','FZS', '1000','T115/2010','XV250/98 FZ6-S','DT175/XT225','MT01','XT250/500/600','DT125/175/RX115','YZF-R1/04','XV750','YZFR15/10','RX115/DT200','XT350K/XV250',
                    'YFZ450R','YZ250N/01','YZF-R1/04','YZ250/XT660R','YBR250/FZ-16','XTZ250/2011','/FZ-16','FZ-16','XT660R-Z','XTZ250/SZ/R15','FZ-16/FZ15','YBR125/XTZ250','YZ250/YZF-R15','5C91/5P42/FZ16','5C91/5P42/FZ-16',
                    'XTZ125/250','YBR1251BV1/R15','YA90/T110/YW100/R15','RXS99','XF650', 'MT60','FAZER','XT225/XT200','XJ6-N','TTR110E','RX00/115','YZ450FV','2PB3YZ','T115FSE','TT10E','22DTS', 'DT175EF','22P1/2/3','RX115/RX100A',
                    'XV250/98','R1/04','XT600/XV25/YFM35','RX115/','YZR-R3','1YZFR15','3C11/10','T110ER','RX100A/RXS115','/XT660X','5C9','/YFM700R','XT600Z','V80/YFM50S','AT135','5GE3','T110R','YFA1', 'YFM125G','4B41/4B51','YW100/NEXT',
                    'AF115S','NEXT/CY50/YA90','YP250', 'MAJESTIC','YFM7FGP','NEXT/YA90','DT125/175EFGK','DT125/175EFGK','MT90','YZF-R6R/08','B8V','DT125/175/XTZ125','YBR/07','FZ6S','XV1700','YFM700F','YBR12ESD','BBL2','YBR125/ZTZ125',
                    'MTN250','YFZ450','1SV2','1SV2','XTZ125/250','2DU','YZF-R15','XT1200ZEZ','58P8','XTZ1200Z','X-MAX','/FZ1-S','B5W4','2BN1/2','58P','XJ6N/2010','SR400/R3','NARANJA','XVS950CU','YZF155','XT350/600','FZ750','B8V',
                    'DT125/99','/SZ-R','DT125/94-04','MTN690-A','FZ15ST','/XJ6-N','MTN850','DT125/94','DT125/98-02','YW125/11','FZ6','YP400','RX115/RX100A/T110E','YP400','FZ6','RX115/RX100A/T110E','FS80/V80/LB80/YB10',
                    '/TDM900','XT225/DT12','XT225/XT600','XTZ150SED','XT350','DT125/175EFGK','DT/100/125/1','YZ450F/07','RX110/RXS115','FZR-1000','DT200/XT660R','DT125/75','/FZ8-N/FZ8-S','WR450','TT-R50','XTZ150SED','58P4/6','5C92/93',
                    '58P6','DT100/125/175K','/XV250','YW125DX','TTR110','XV535S','RXS115/XT660','DT100K/RX115L','RX100A','YZ125/250/450','DT200/XT225','DT75/98','/YBR125SS','YC110','1BN3/4','XT1200ZEZ','YBR1251BV1/R15','5C91/5P42/FZ-16',
                    'V80/YA90','5P42/FZ-16','99/XT660R/FZ-16','99/XT660R/FZ-16','MTT690-A','/XT660X','TT-R110E','YFM80','2012','R15/FZ16ST','/YXR700F','YFM660/700G','AF115S/T115','AT135','FZ1S',' XJ6N/2010','B121','MT01/XT1200Z','MTN250',
                    'DT12','XT350/XT660R','DT100/XT660R','DT125/175AZU','DT125/175ROJ','/FZ1-S','MTN320','RACEBLU','1SV','1SV2','45D8','GPX','45D7','2CD2','YBR125SD','T110E/CY50','/FAZER-16/FZ-16','DT100/RX100/',
                    'XT600/DT125','YBR250/LIBER12','94/T110','BLACK/BROWN','DB/BEIGE', '2BN1/2','BBE','YBR/07','2P63','YP250','DT200/125/175','XT225/XTZ250','DT125/XT225','YB/V80','V80/DT100','DT125/RX100/','2DR7',
                    '2DR4','VIOLETA','BLACK','T110/NEXT','XTZ150SED','XT350/DT125/','V110/T110','DT200/XT225','YFM700G','XT225/DT200','YBR125/08','YBR12ESD','5P42/5C92/FZ-16','5P42/5C92/FZ-16','DT125/XT225','RX115/','T11/V80/R',
                    'YFZR15/FZ16','FZ16/FZ15','R6S','YBR/07','RX100/5C9','RX100/5P42','DT1','YZF155','YFM-125-A','DTS','XTZ250/2011','TDM850/900','YZF-R6R/08','XJ6F','FZ-6S','YZF-','R15-V2','XTZ125/250','XTZ1200Z','DT125/T110/NEXT',
                    'XVS650','XT660R-Z','TRASYZF-R3','XVS950/XT1200Z','5P42/FZ-16','YBR125ED','5P42/FZ-16','DT200/RX115/XV250','DT125/175/YZF-R3','MAX','2NMAX','XTZ1125','BF21/2016','AF115S/T115','XTZ150SE','XTZ1','XT225/XT600',
                    'DT200/97/RX115','DT125/99','YZF-R4','20D1/2007','FZ-16/FZ15','/2011','XT1200ZEZ']

def remove(x,PALABRAS_ELIMINAR):
  palabras = str(x).split()
  reformado = ['' if palabra in PALABRAS_ELIMINAR else palabra for palabra in palabras]
  texto = " ".join(reformado)
  return texto

dataset.Descripcion_producto_procesada = dataset.Descripcion_producto_procesada.apply(lambda x: remove(x,eliminar)) 
dataset.Descripcion_producto_procesada = dataset.Descripcion_producto_procesada.apply(lambda x: x.strip()) 
dataset['Key_definitivo'] = dataset['Key_definitivo'].astype(str)

df=dataset.groupby(['Key_definitivo','Descripcion_producto_procesada']).agg({'Descripcion_producto_procesada':'count'})
df.rename(columns={'Descripcion_producto_procesada':'conteo'}, inplace=True)
df.reset_index(inplace=True)
df.sort_values(by=['Key_definitivo','conteo'],ascending=[False,False],inplace=True)
df.drop_duplicates('Key_definitivo',keep='first',inplace=True)

df_final=pd.merge(dataset,df,how='left',on='Key_definitivo')
df_final=df_final.rename(columns={"Descripcion_producto_procesada_y":'Descripcion_key_definitivo','Descripcion_producto_procesada_x':'Descripcion_producto_procesada'})


# APLICACIÒN 
#opciones1=['Seleccione','Análisis general','Análisis por key']
#selectbox1 = st.sidebar.selectbox('¿Qué desea hacer?',opciones1)


st.markdown("---")

st.header('Análisis general')

#if selectbox1=='Análisis general':
options = ['Pais_Origen','Categoria','Nombre_GrupoClasificacion','Color','Categoria_Producto_Repuesto','Codigo_sintoma','Condicion','Ciudad_reclamacion','Centro_de_responsabilidad_reclamacion','AñoMes_dictamen']
column_1, column_2 = st.columns(2)
with column_1: 
  selected_option = st.selectbox("Con qué variable desea filtrar los datos:", options)
with column_2:
  opciones_vbles_completas = pd.unique(df_final[selected_option].dropna())
  if selected_option=='Codigo_sintoma' or selected_option=='Condicion':
    opciones_vbles=[]
    for x in opciones_vbles_completas:      
      if len(x)==2:
        opciones_vbles.append(x)
  else:
    opciones_vbles = pd.unique(df_final[selected_option].dropna())
  vble_seleccionada = st.selectbox("Seleccione:", opciones_vbles)
 
data_filtered=df_final[df_final[selected_option]==vble_seleccionada] # eliminados y reemplazados


column_6, column_7 = st.columns(2)
with column_6:
  if selected_option!='Nombre_GrupoClasificacion':   
    Modelos=data_filtered.groupby(["NombreComercial"])[['Numero_de_motor','Numero_solicitud']].nunique().reset_index().sort_values('Numero_de_motor', ascending=False)
    Modelos.rename(columns={'Numero_de_motor':'Cant motores', 'Numero_solicitud':'Cant PSER'}, inplace=True)
    px.defaults.width = 750 
    px.defaults.height = 450
    fig = px.bar(Modelos.sort_values('Cant PSER', ascending=False).iloc[0:20], x='NombreComercial',y='Cant PSER',color='NombreComercial', labels={"Cant PSER": "Cantidad PSER",  "NombreComercial": "Modelo"})
    fig.update_layout(showlegend=False)
    st.subheader("**Cantidad PSER por modelos motocicleta**")
    st.plotly_chart(fig)  

with column_7:
  Top=data_filtered.groupby(["Key_definitivo","Descripcion_key_definitivo"])[['Numero_de_motor','Numero_solicitud']].nunique().reset_index().sort_values('Numero_de_motor', ascending=False).head(15)  
  Top.rename(columns={'Numero_de_motor':'Cant motores', 'Numero_solicitud':'Cant PSER'}, inplace=True)
  st.subheader("**Top 15 productos más demandados**")
  st.write(Top.assign(hack='').set_index('hack'))

checkbox = st.radio("Quiere verlo por modelo:", ("Si", "No"))
if checkbox=="Si":
  opciones_modelo = pd.unique(data_filtered['NombreComercial'])
  modelo_seleccionado = st.selectbox("Seleccione modelo:", opciones_modelo)
  data_filtered_modelo=data_filtered[data_filtered['NombreComercial']==modelo_seleccionado]
  resumen_d=data_filtered_modelo.groupby(['NombreComercial',"Descripcion_key_definitivo"])[['Numero_de_motor','Numero_solicitud']].nunique().reset_index().sort_values('Numero_de_motor', ascending=False)
  resumen_id=data_filtered_modelo.groupby(["Key_definitivo",'Descripcion_key_definitivo'])[['Numero_de_motor','Numero_solicitud']].nunique().reset_index().sort_values('Numero_de_motor', ascending=False)  
     
    
  st.subheader('Top 30 repuestos para atender garantías del modelo')
  px.defaults.width = 1400
  px.defaults.height = 500
  fig = px.bar(resumen_id.iloc[0:30], x='Descripcion_key_definitivo',y='Numero_de_motor',color='Key_definitivo', labels={"Numero_de_motor": "Cantidad",  "Descripcion_key_definitivo": "Producto"})
  #fig.update_xaxes(tickangle=40)
  st.plotly_chart(fig) 
  
  with st.expander('Ver tabla del gráfico'):
    st.subheader('Tabla resumen')
    st.dataframe(resumen_id.assign(hack='').set_index('hack')) 

  st.header('Análisis por key')
  column_3, column_4, column_5= st.columns(3)
  with column_3:
    checkbox = st.radio("Método de entrada Key:", ('Todos',"Selección lista desplegable", "Ingresar key"))
  with column_4:
    if checkbox=="Selección lista desplegable":
      opciones_key=pd.unique(data_filtered_modelo['Key_definitivo'])
      key_seleccionado = st.selectbox("Seleccione:", opciones_key)
      filtro=data_filtered_modelo[data_filtered_modelo['Key_definitivo']==key_seleccionado]
    elif checkbox=="Ingresar key":
      key_seleccionado=st.text_input('Ingrese el key')
      filtro=data_filtered_modelo[data_filtered_modelo['Key_definitivo']==key_seleccionado]
    else:
      filtro=data_filtered_modelo.copy()
  with column_5:
    checkbox1 = st.radio("Ver por color:", ("Si", "No"))

  if checkbox1=="Si":
    filtro['color_pred']=filtro['Color'].apply(lambda x: x.split(maxsplit=1)[0])
    Top15=filtro.groupby(['NombreComercial',"Color"])[['Numero_de_motor','Numero_solicitud']].nunique().reset_index().sort_values('Numero_de_motor', ascending=False)
    Tiempo=filtro.groupby(["Color"]).agg({'tiempo_venta':['mean','min','max','median',]}).reset_index()
    Tiempo.columns = ['Color','prom_tiempo_falla','min_tiempo_falla','max_tiempo_falla','median_tiempo_falla']
    Tiempo['prom_tiempo_falla'] = Tiempo['prom_tiempo_falla'].astype(int)
    Tiempo['median_tiempo_falla'] = Tiempo['median_tiempo_falla'].astype(int)
    
    st.subheader("**Top 15**")
    st.text('El top 15 de los casos que han presentado garantías asociadas a este key producto:')
    Top_final=pd.merge(Top15, Tiempo, how='left', on='Color')
    Top_final.drop(['NombreComercial'],axis=1, inplace=True)
    st.write(Top_final.assign(hack='').set_index('hack'))

  else:
    Top15=filtro.groupby(['NombreComercial'])[['Numero_de_motor','Numero_solicitud']].nunique().reset_index().sort_values('Numero_de_motor', ascending=False)
    Tiempo=filtro.groupby(["NombreComercial"]).agg({'tiempo_venta':['mean','min','max','median',]}).reset_index()
    Tiempo.columns = ['NombreComercial','prom_tiempo_falla','min_tiempo_falla','max_tiempo_falla','median_tiempo_falla']
    Tiempo['prom_tiempo_falla'] = Tiempo['prom_tiempo_falla'].astype(int)
    Tiempo['median_tiempo_falla'] = Tiempo['median_tiempo_falla'].astype(int)

    st.subheader("**Top 15**")
    st.text('El top 15 de los casos que han presentado garantías asociadas a este key producto:')
    Top_final=pd.merge(Top15, Tiempo, how='left', on='NombreComercial')
    Top_final.drop(['NombreComercial'],axis=1, inplace=True)
    st.write(Top_final.assign(hack='').set_index('hack'))

  
else:
  resumen_d=data_filtered.groupby(['Key_definitivo',"Descripcion_key_definitivo"])[['Numero_de_motor','Numero_solicitud']].nunique().reset_index().sort_values('Numero_de_motor', ascending=False)
  resumen_id=data_filtered.groupby(["Key_definitivo"])[['Numero_de_motor','Numero_solicitud']].nunique().reset_index().sort_values('Numero_de_motor', ascending=False)
  column_1, column_2 = st.columns(2)
  px.defaults.width = 1400
  px.defaults.height = 500
  fig = px.bar(resumen_d.sort_values('Numero_solicitud', ascending=False).iloc[0:30], x='Descripcion_key_definitivo',y='Numero_solicitud',color='Key_definitivo', labels={"Numero_solicitud": "Cantidad PSER",  "Descripcion_key_definitivo": "Producto"})
  st.subheader('**Top 30 productos más demandados para atender garantías**')
  st.plotly_chart(fig) 
    
  #st.subheader('Tabla cantidad PSER y motores')
  #st.write(resumen_d.assign(hack='').set_index('hack'))
  #st.dataframe(resumen_d)

  st.header('Análisis por key')
  column_3, column_4, column_5= st.columns(3)
  with column_3:
    checkbox = st.radio("Método de entrada Key:", ('Todos',"Selección lista desplegable", "Ingresar key"))
  with column_4:
    if checkbox=="Selección lista desplegable":
      opciones_key=pd.unique(data_filtered['Key_definitivo'])
      key_seleccionado = st.selectbox("Seleccione:", opciones_key)
      filtro=data_filtered[data_filtered['Key_definitivo']==key_seleccionado]
    elif checkbox=="Ingresar key":
      key_seleccionado=st.text_input('Ingrese el key')
      filtro=data_filtered[data_filtered['Key_definitivo']==key_seleccionado]
    else:
      filtro=data_filtered.copy()
  with column_5:
    checkbox1 = st.radio("Ver por color:", ("Si", "No"))

  if checkbox1=="Si":
    filtro['color_pred']=filtro['Color'].apply(lambda x: x.split(maxsplit=1)[0])
    Top15=filtro.groupby(['NombreComercial',"Color"])[['Numero_de_motor','Numero_solicitud']].nunique().reset_index().sort_values('Numero_de_motor', ascending=False)
    Tiempo=filtro.groupby(["Color"]).agg({'tiempo_venta':['mean','min','max','median',]}).reset_index()
    Tiempo.columns = ['Color','prom_tiempo_falla','min_tiempo_falla','max_tiempo_falla','median_tiempo_falla']
    Tiempo['prom_tiempo_falla'] = Tiempo['prom_tiempo_falla'].astype(int)
    Tiempo['median_tiempo_falla'] = Tiempo['median_tiempo_falla'].astype(int)
    
    st.subheader("**Top 15**")
    st.text('El top 15 de los casos que han presentado garantías asociadas a este key producto:')
    Top_final=pd.merge(Top15, Tiempo, how='left', on='Color')
    #Top_final.drop(['NombreComercial'],axis=1, inplace=True)
    st.write(Top_final.assign(hack='').set_index('hack'))

  else:
    Top15=filtro.groupby(['NombreComercial'])[['Numero_de_motor','Numero_solicitud']].nunique().reset_index().sort_values('Numero_de_motor', ascending=False)
    Tiempo=filtro.groupby(["NombreComercial"]).agg({'tiempo_venta':['mean','min','max','median',]}).reset_index()
    Tiempo.columns = ['NombreComercial','prom_tiempo_falla','min_tiempo_falla','max_tiempo_falla','median_tiempo_falla']
    Tiempo['prom_tiempo_falla'] = Tiempo['prom_tiempo_falla'].astype(int)
    Tiempo['median_tiempo_falla'] = Tiempo['median_tiempo_falla'].astype(int)

    st.subheader("**Top 15**")
    st.text('El top 15 de los casos que han presentado garantías asociadas a este key producto:')
    Top_final=pd.merge(Top15, Tiempo, how='left', on='NombreComercial')
    #Top_final.drop(['NombreComercial'],axis=1, inplace=True)
    st.write(Top_final.assign(hack='').set_index('hack'))

  

st.header('Similitudes modelos')
df_features=pd.read_excel('caracteristicas_tecnicas.xlsx')
Fecha=st.date_input('Ingrese la fecha en que entraría al mercado:')
Unidades=st.number_input('Ingrese el número de motocicletas que se venderían en el año:')
variables = ['potencia','torque','precio', 'cilindraje', 'discos', 'alimentacion','refrigeracion', 'arranque','sistema frenos']
#default = ['precio', 'cilindraje']

variables_similitud = st.multiselect(label="Seleccione las variables a comparar", options=variables)
df_features_filtro=pd.DataFrame()
df_features_filtro['NombreComercial']=df_features['nombre comercial']
ensayo=list()
if variables_similitud is not None:
  for count, value in enumerate(variables_similitud):
    if value=='precio':
      precio=st.number_input('Ingrese el precio:')
      df_features_filtro['precio']=df_features['precio']
      df_features_filtro['% precio']= df_features_filtro['precio'].apply(lambda x: x/precio if x < precio else precio/x )  
      ensayo.append((len(df_features_filtro.columns)-1))
    if value =='cilindraje':
      cilindraje=st.number_input('Ingrese el cilindraje:')
      df_features_filtro['cilindraje']=df_features['cilindraje']
      df_features_filtro['% cilindraje']= df_features_filtro['cilindraje'].apply(lambda x: x/cilindraje if x < cilindraje else cilindraje/x ) 
      ensayo.append((len(df_features_filtro.columns)-1))
    if value=='potencia':
      potencia=st.number_input('Ingrese la potencia (en Hp multiplicado por las RPM):')
      df_features_filtro['potencia']=df_features['potencia']
      df_features_filtro['% potencia']= df_features_filtro['potencia'].apply(lambda x: x/potencia if x < potencia else potencia/x )   
      ensayo.append((len(df_features_filtro.columns)-1))
    if value == 'torque':
      torque=st.number_input('Ingrese el torque (en Nm multiplicado por las RPM):')
      df_features_filtro['torque']=df_features['torque']
      df_features_filtro['% torque']= df_features_filtro['torque'].apply(lambda x: x/torque if x < torque else torque/x )   
      ensayo.append((len(df_features_filtro.columns)-1))
    if value=='discos':
      discos=st.radio('Ingrese si tiene 1 o 2 frenos de disco:', ("1", "2"))
      df_features_filtro['discos']=df_features['discos']
      df_features_filtro['% discos']= df_features_filtro['discos'].apply(lambda x: x/discos if x < discos else discos/x )
      ensayo.append((len(df_features_filtro.columns)-1))
    if value=='alimentacion':
      alimentacion=st.radio('Ingrese si es carburador o inyección:', ("carburador", "inyeccion"))
      df_features_filtro['alimentacion']=df_features['alimentacion']
      df_features_filtro['% alimentacion']= df_features_filtro['alimentacion'].apply(lambda x: 1 if x == alimentacion else 0.5 )
      ensayo.append((len(df_features_filtro.columns)-1))
    if value=='refrigeracion':
      refrigeracion=st.radio('Ingrese si la refrigeración es aire o liquida:', ("Aire", "Liquido"))
      df_features_filtro['refrigeracion']=df_features['refrigeracion']
      df_features_filtro['% refrigeracion']= df_features_filtro['refrigeracion'].apply(lambda x: 1 if x == refrigeracion else 0.5 )
      ensayo.append((len(df_features_filtro.columns)-1))
    if value=='arranque':
      arranque=st.radio('Ingrese si tiene arranque eléctrico o es pedal:', ("Eléctrico", "Pedal",'Eléctrico y pedal'))
      df_features_filtro['arranque']=df_features['arranque']
      df_features_filtro['% arranque']= df_features_filtro['arranque'].apply(lambda x: 1 if x == arranque else 0.33 )
      ensayo.append((len(df_features_filtro.columns)-1))
    if value=='sistema frenos':
      frenos=st.radio('Ingrese si tiene frenos ABS o convencionales:', ("ABS", "Convencionales"))
      df_features_filtro['sistema frenos']=df_features['sistema frenos']
      df_features_filtro['% sistema frenos']= df_features_filtro['sistema frenos'].apply(lambda x: 1 if x == frenos else 0.5 )
      ensayo.append((len(df_features_filtro.columns)-1))

if (st.button('Calcular similitudes')):
  arr = np.array(ensayo)
  prom=df_features_filtro.iloc[:,arr]
  df_features_filtro['% promedio']=prom.mean(axis=1)
  df_features_filtro.sort_values(by='% promedio', ascending=False, inplace=True)
  st.write(df_features_filtro)

st.markdown('**Por favor seleccione el modelo que considera más similar**')
st.text('Puede ser basado en el % de similitud arrojado por el cálculo o el que usted con su conocimiento considere más apropiado')
column_8, column_9= st.columns(2)
with column_8:
  opciones = pd.unique(df_final['NombreComercial'])
  modelo_similar = st.selectbox("Seleccione modelo más similar:", opciones)
with column_9:
  porc_similitud=st.number_input('Ingrese porcentaje similitud:')

data_modelo_similar=df_final[df_final['NombreComercial']==modelo_similar]
mensual=data_modelo_similar.groupby(['Key_definitivo', pd.Grouper(key='Fecha_dictamen_tecnico', freq='M')])[['Cantidad']].sum().reset_index()
mensual.sort_values(by='Cantidad', ascending=False, inplace=True)
mediana_mes=mensual.groupby('Key_definitivo')[['Cantidad']].median().reset_index().rename(columns={'Cantidad':'cantidad_rpto_mes'})
mediana_mes['cantidad_rpto_mes']=mediana_mes['cantidad_rpto_mes'].astype(int)
mediana_mes.sort_values(by='cantidad_rpto_mes', ascending=False, inplace=True)

resumen_key=data_modelo_similar.groupby(['NombreComercial','Key_definitivo','Descripcion_key_definitivo'])[['Numero_de_motor','Numero_solicitud']].nunique().reset_index().sort_values('Numero_de_motor', ascending=False)


runt = pd.read_csv("Runt_proporcion.csv", sep=";" ,encoding= 'unicode_escape')
listado = pd.merge(resumen_key, runt, how='left',on='NombreComercial')
listado['Proporcion_motos_falla']=listado['Numero_de_motor']/listado['Total_runt']



Tiempo_falla=data_modelo_similar.groupby(['NombreComercial','Key_definitivo','Descripcion_key_definitivo']).agg({'tiempo_venta':['mean','min','max','median',]}).reset_index()
Tiempo_falla.columns = ['NombreComercial','Key_definitivo','Descripcion_key_definitivo','prom_tiempo_falla','min_tiempo_falla','max_tiempo_falla','median_tiempo_falla']
Tiempo_falla['prom_tiempo_falla'] = Tiempo_falla['prom_tiempo_falla'].astype(int)
Tiempo_falla['median_tiempo_falla'] = Tiempo_falla['median_tiempo_falla'].astype(int)


temporal=pd.merge(listado, Tiempo_falla, how='left', on=['NombreComercial','Key_definitivo','Descripcion_key_definitivo'])

final=pd.merge(temporal, mediana_mes, how='left',on='Key_definitivo')
final['cantidad_rpto_mes'] = final['cantidad_rpto_mes'].astype(int)
final['fecha_futura'] = final['median_tiempo_falla'].apply(lambda x: timedelta(days = x) + Fecha)


final.drop(['NombreComercial','prom_tiempo_falla','min_tiempo_falla','max_tiempo_falla'], axis=1, inplace=True)
final.rename(columns={'median_tiempo_falla':'tiempo_falla'}, inplace=True)
final['resultado']=final['Proporcion_motos_falla']*porc_similitud*Unidades
final['resultado'] = final['resultado'].astype(int)
final['repuestos_a_tener']=final['cantidad_rpto_mes']*porc_similitud
final['repuestos_a_tener']= final['repuestos_a_tener'].astype(int)
st.dataframe(final.head(50))


with st.expander('Tablas soporte'):
  st.write(mediana_mes)
  st.write(Tiempo_falla)
  st.write(listado)

