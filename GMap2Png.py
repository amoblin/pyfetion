# coding=utf-8

import math
import os
import urllib2
import Image

from random import randint

def getMercatorLatitude(lati, zoom):
    
    maxlat = math.pi
    lat = lati
   
    if (lat > 90):
        lat = lat - 180
    if (lat < -90):
        lat = lat + 180

    #转换度数到弧度
    phi = math.pi * lat / 180.0;

    res = 0.5 * math.log((1 + math.sin(phi)) / (1 - math.sin(phi)))
    maxTileY = math.pow(2, zoom)
    result = (int)(((1 - res / maxlat) / 2) * (maxTileY))

    return result;


def getTile(longitude, latitude, zoom):

    longitude=180+longitude
    
    longTileSize=360.0/(pow(2,zoom))

    tilex =  longitude/longTileSize

    tiley = getMercatorLatitude(latitude, zoom)

    tilex = int(math.floor(tilex))

    tiley = int(math.floor(tiley))

    return (tilex, tiley)

    
def GMap2Png(longitude1, latitude1, longitude2, latitude2, zoom, savename=None):

    (x1, y1) = getTile(longitude1,latitude1,zoom)
    (x2, y2) = getTile(longitude2,latitude2,zoom)
    z = zoom

    print x1,y1
    print x2,y2

    print ((x2-x1+1)*256, (y2-y1+1)*256)

    for x in range(x1,x2+1):
        for y in range(y1,y2+1):
            #print x,y
            filename = "v=cn1.11&hl=zh-CN&x=%d&y=%d&z=%d&s=Galile" % (x,y,z)
            if not os.path.isfile(filename+".png"):
                try:
                    #随机选择一个服务器
                    #避免连续向一个服务器发送请求
                    data = urllib2.urlopen("http://mt%d.google.cn/mt/" % randint(0,3)+filename).read()
                except urllib2.HTTPError, e:
                    print 'Error code: ',e.code
                    return False
                except urllib2.URLError, e:
                    print 'Reason: ', e.reason
                    return False

                f = file(filename+".png","wb")
                f.write(data)
                f.close()
   

    Map = Image.new("RGB", ((x2-x1+1)*256, (y2-y1+1)*256))
    for x in range(x1,x2+1):
        for y in range(y1,y2+1):
            #print x,y
            filename = "v=cn1.11&hl=zh-CN&x=%d&y=%d&z=%d&s=Galile" % (x,y,z)
           #把得到的分块合并
            box = ((x-x1)*256, (y-y1)*256, (x-x1)*256+256, (y-y1)*256+256)
            #print box
            im = Image.open(filename+".png")
            Map.paste(im, box)

    temp = "temp_map.png"
    Map.save(temp)
    del Map
    print "converting"
    Map = Image.open(temp)
    Map = Map.convert("P", palette=Image.ADAPTIVE)
    if not savename:
        Map.save("New_GMap2Png_Map"+str(zoom)+".png", optimize=True)
    else:
        Map.save(savename+".png")
    return True


#西安
#GMap2Png(108.80824,34.37075,109.10316,34.15366,16)


GMap2Png(118.7015, 30.99653, 118.82008, 30.90867, 18, "xuechen18")
