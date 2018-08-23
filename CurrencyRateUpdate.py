from suds.client import Client
from suds.xsd.doctor import Import, ImportDoctor
from xmlrpc.client import ServerProxy
import datetime
import xml.etree.ElementTree
from datetime import datetime


INDICADOR_VENTA = 318
username = 'cewongq@gmail.com' #the user
pwd = '3ntrando'      #the password of the user
dbname = 'odoo'    #the database
currentDate = datetime.now().date()
partername = 'Prueba API ' + currentDate.isoformat()


#Get USD exchange rate from CRC
today = currentDate.strftime('%d/%m/%Y')

initialDate = "14/08/2018"

imp = Import('http://www.w3.org/2001/XMLSchema', location='http://www.w3.org/2001/XMLSchema.xsd')
imp.filter.add('http://ws.sdde.bccr.fi.cr')

client = Client('http://indicadoreseconomicos.bccr.fi.cr/indicadoreseconomicos/WebServices/wsIndicadoresEconomicos.asmx?WSDL', doctor=ImportDoctor(imp))


response = client.service.ObtenerIndicadoresEconomicosXML(tcIndicador='318', tcFechaInicio=initialDate, tcFechaFinal=today, tcNombre='pruebas', tnSubNiveles='N')
xmlResponse = xml.etree.ElementTree.fromstring(response)
sellingRateNodes = xmlResponse.findall("./INGC011_CAT_INDICADORECONOMIC/NUM_VALOR")

response = client.service.ObtenerIndicadoresEconomicosXML(tcIndicador='317', tcFechaInicio=initialDate, tcFechaFinal=today, tcNombre='pruebas', tnSubNiveles='N')
xmlResponse = xml.etree.ElementTree.fromstring(response)
buyingRateNodes = xmlResponse.findall("./INGC011_CAT_INDICADORECONOMIC/NUM_VALOR")

xmlResponse = xml.etree.ElementTree.fromstring(response)
datesNodes = xmlResponse.findall("./INGC011_CAT_INDICADORECONOMIC/DES_FECHA")

nodeIndex = 0
nodesLength = len(datesNodes)

while nodeIndex < nodesLength:
    sellingOriginalRate = float(sellingRateNodes[nodeIndex].text)
    sellingRate = 1/sellingOriginalRate

    buyingOriginalRate = float(buyingRateNodes[nodeIndex].text)
    buyingRate = 1/buyingOriginalRate
    
    dateNode = datesNodes[nodeIndex].text
    rateDate = datetime.strptime( dateNode, "%Y-%m-%dT%H:%M:%S%z" ).strftime("%Y-%m-%d")


    # Get the uid
    sock_common = ServerProxy ('http://odoo.akurey.com:8069/xmlrpc/common')
    uid = sock_common.login(dbname, username, pwd)

    #replace localhost with the address of the server
    sock = ServerProxy('http://odoo.akurey.com:8069/xmlrpc/object')

    rate = {
    'name': rateDate,
    'rate': sellingRate, 
    'original_rate':sellingOriginalRate, 
    'rate_2':buyingRate, 
    'original_rate_2':buyingOriginalRate, 
    'currency_id': 3
    }
    #try:
    ratesIds = sock.execute(dbname, uid, pwd, 'res.currency.rate', 'search', [['name', '=', rateDate]])
    
    if len(ratesIds) > 0:
        rate_id = sock.execute(dbname, uid, pwd, 'res.currency.rate', 'write', ratesIds[0], {'rate': sellingRate, 'original_rate':sellingOriginalRate, 'rate_2':buyingRate, 'original_rate_2':buyingOriginalRate})
        if rate_id > 0 :
            print("rate sucesfully updated " + rateDate)
    else:
        rate_id = sock.execute(dbname, uid, pwd, 'res.currency.rate', 'create', rate)
        if rate_id > 0 :
            print("rate sucesfully created " + rateDate)

    
    
    #except ValidationError:

    nodeIndex += 1

