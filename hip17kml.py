#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
#import cgi
import logging
import simplekml
import h3
import hip17
import csv

sc=hip17.scale_calculator()

def get_hotspots(h3hex,kml):
    ''' helper funtion to populate points for all hotspots in h3hex to kml file
    input: h3hex of interest and kml class
    returns kml populated with hotspots in the hex and its neighbours
    '''

    df = sc.get_hotspots(h3hex)
    h3res=h3.h3_get_resolution(h3hex)
    #print(df.columns)
    #print(df)
    for index, row in df.iterrows():
        pnt=kml.newpoint(name=row["name"], coords=[(row["longitude"],row["latitude"],row["height"])],extrude=1)
        #pnt.description='Scaling = '+str(row["scaling"])
        if h3res < 7:
            pnt.style.labelstyle.scale=0
        else:
            pnt.style.labelstyle.scale=0.8
        pnt.extendeddata.newdata(name='Scaling', value=row["scaling"], displayname='Scaling from API')
        pnt.extendeddata.newdata(name='Online', value=row["online"], displayname='Online')
        #pnt.altitudemode='relativeToGround'
        pnt.style.iconstyle.scale = 0.8  # Icon thrice as big
        #pnt.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png'
        #pnt.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png'

    df = sc.get_inactive_hotspots(h3hex)
    for index, row in df.iterrows():
        pnt=kml.newpoint(name=row["name"], coords=[(row["longitude"],row["latitude"],row["height"])],extrude=1)
        #pnt.description='Scaling = '+str(row["scaling"])
        pnt.style.iconstyle.scale = 0.5
        pnt.style.labelstyle.scale=0
        pnt.style.labelstyle.color = 'ff0000ff'  # Red
        pnt.extendeddata.newdata(name='Scaling', value=row["scaling"], displayname='Scaling from API')
        pnt.extendeddata.newdata(name='Online', value=row["online"], displayname='Online')


        pnt.style.iconstyle.scale = 0.7  # Icon thrice as big
        #pnt.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png'
        pnt.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle_highlight.png'
        #pnt.style.iconstyle.icon.href = None

    df = sc.get_neighbour_hotspots(h3hex)
    #print('neighbours',df)
    for index, row in df.iterrows():
        pnt=kml.newpoint(name=row["name"], coords=[(row["longitude"],row["latitude"],row["height"])],extrude=1)
        #pnt.description='Scaling = '+str(row["scaling"])
        
        pnt.style.labelstyle.scale=0
        pnt.style.labelstyle.color = 'ff0000ff'  # Red
        pnt.extendeddata.newdata(name='Scaling', value=row["scaling"], displayname='Scaling from API')
        pnt.extendeddata.newdata(name='Online', value=row["online"], displayname='Online')


        pnt.style.iconstyle.scale = 0.7  # Icon thrice as big
        #pnt.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png'
        pnt.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png'
        #pnt.style.iconstyle.icon.href = None
    return kml
    

def geth3polys(lat,lng,alt):
    # i'm sure there is a much more elegant way to do this
    # i assume these are meters so this may not work if set to feet
    # or maybe other localizations such as screen resolution
    neighbours=[]
    scale=0
    #print('altitude ',alt)
    if alt > 4000000:
        res=0
        rings=2
    elif alt >1600000:
        res=1
        rings=2
    elif alt >540000:
        res=2
        rings=3
    elif alt >175000:
        res=3
        rings=3
    elif alt >65000:
        res=4
        rings=4
    elif alt >30000:
        res=5
        rings=5
    elif alt >10000:
        res=6
        rings=6
    elif alt >3800:
        res=7
        rings=7
    elif alt >1800:
        res=8
        rings=8
    elif alt >1400:
        res=9
        rings=9
    elif alt >600:
        res=10
        rings=10
    elif alt >150:
        res=11
        rings=11
    elif alt >50:
        res=12
        rings=12
    else:
        res=0
        rings=12

    # check if we're within range of hip17 hexes
    if res>3 or res<13:
        h3hex=h3.geo_to_h3(lng,lat,res)
        scale_factor=sc.get_scale(h3hex)
        scale=sc.scale_dict#sc.get_scale(h3hex)
        neighbours=sc.get_neighbours(h3hex)

    # Create new kml file to send to ge
    kml=simplekml.Kml(name='HIP17 Sim')

    # Create mulitpolygons for kml 
    mpoly=[]
    for i in range(0,7):
        mpoly.append(kml.newmultigeometry(name='Unoccupied Neighbours'))
    mpolysmall = kml.newmultigeometry(name='Small H3')
    mpolyhome = kml.newmultigeometry(name='Home Hex')
    mpoly_neigh=[]
    for i in range(0,7):
        mpoly_neigh.append(kml.newmultigeometry(name='Occupied Neighbours'))

    # generate home hex centered around the cameras center of view
    home_hex=h3.geo_to_h3(lng,lat,res)#12)

    # draw the neighbouring hexes
    i=0
    j=0
    for key in neighbours:
        if neighbours[key]['occupied']:
            gjhex_neigh=h3.h3_to_geo_boundary(key,geo_json=True)
            pol_neigh=mpoly_neigh[i].newpolygon(name=key,
                                             extrude=True,
                                outerboundaryis=gjhex_neigh)
            pol_neigh.style.linestyle.width = 2
            pol_neigh.style.linestyle.color = simplekml.Color.white
            pol_neigh.style.polystyle.color = simplekml.Color.changealphaint(150, simplekml.Color.white)
            pol_neigh.style.balloonstyle.bgcolor = simplekml.Color.white
            pol_neigh.style.balloonstyle.textcolor = simplekml.Color.rgb(0, 0, 255)
            mpoly_neigh[i].extendeddata.newdata(name='h3hex', value=key, displayname='h3hex')
            mpoly_neigh[i].extendeddata.newdata(name='active_hotspots', value=neighbours[key]['num_hs'], displayname='num of active hotspots')
            i+=1           
        else: # unoccupied neighbour hex
            gjhex=h3.h3_to_geo_boundary(key,geo_json=True)
            pol=mpoly[j].newpolygon(name=key,
                                 extrude=True,
                                 outerboundaryis=gjhex)
            pol.style.linestyle.width = 2
            pol.style.linestyle.color = simplekml.Color.white
            pol.style.polystyle.color = simplekml.Color.changealphaint(1, simplekml.Color.white)
            pol.style.balloonstyle.bgcolor = simplekml.Color.white
            pol.style.balloonstyle.textcolor = simplekml.Color.rgb(0, 0, 255)
            mpoly[j].extendeddata.newdata(name='h3hex', value=key, displayname='h3hex')
            mpoly[j].extendeddata.newdata(name='active_hotspots', value=neighbours[key]['num_hs'], displayname='num of active hotspots')
            j+=1
        
            
    # generate the smaller hex rings centered around the cameras center of view
    home_hex_small=h3.geo_to_h3(lng,lat,res+1)#12)
    ring_small=h3.k_ring(home_hex_small,1)
    for h in ring_small:
        gjhexsmall=h3.h3_to_geo_boundary(h,geo_json=True)
        polsmall=mpolysmall.newpolygon(extrude=True,
                                outerboundaryis=gjhexsmall)
        polsmall.style.linestyle.width = 0.5
        polsmall.style.polystyle.color = simplekml.Color.changealphaint(1, simplekml.Color.white)

    # create the home hex polygon
    gjhexhome=h3.h3_to_geo_boundary(home_hex,geo_json=True)
    polhome=mpolyhome.newpolygon()

    polhome.extrude=True
    polhome.outerboundaryis=gjhexhome
    polhome.style.linestyle.width = 2
    #polhome.style.polystyle.color = simplekml.Color.changealphaint(200, simplekml.Color.green)
    polhome.style.linestyle.color = simplekml.Color.white #simplekml.Color.changealpha("250", simplekml.Color.orange)
    try:
        if scale[res]['scale'] < 0.2:
            polhome.style.polystyle.color = simplekml.Color.changealpha("75", simplekml.Color.red)
        elif scale[res]['scale'] < 0.8:
            polhome.style.polystyle.color = simplekml.Color.changealpha("75", simplekml.Color.yellow)
        else:
            polhome.style.polystyle.color = simplekml.Color.changealpha("75", simplekml.Color.green)
    except KeyError:
        polhome.style.polystyle.color = simplekml.Color.changealpha("75", simplekml.Color.white)


    # this works but unreadable so just use the .extendeddata method
    '''btext="""<![CDATA[
      <b><font color="#CC0000" size="+3">$[name]</font></b>
      <br/><br/>
      <font face="Courier">$[description]</font>
      <br/><br/>"""+ str(sc.scale_dict[res]) + \
      """<br/><br/>
      <!-- insert the to/from hyperlinks -->
      $[geDirections]
      ]]>"""
    
    
    polhome.style.balloonstyle.text = btext #str(sc.scale_dict[res])
    '''

    polhome.style.balloonstyle.bgcolor = simplekml.Color.white
    polhome.style.balloonstyle.textcolor = simplekml.Color.rgb(0, 0, 255)
    try:
        for key in sc.scale_dict[res]:
            mpolyhome.extendeddata.newdata(name=key, value=sc.scale_dict[res][key], displayname=key)
    except KeyError:
        pass
    #kml=get_hotspots(h3hex,kml)
    kml=get_hotspots(home_hex,kml)

    # create the screen overlay to display the current h3 resolution
    osd=kml.newscreenoverlay()
    osd.name='Resolution'
    osd.overlayxy = simplekml.OverlayXY(x=0,y=1,xunits=simplekml.Units.fraction,
                                       yunits=simplekml.Units.fraction)
    osd.screenxy = simplekml.ScreenXY(x=15,y=15,xunits=simplekml.Units.pixels,
                                     yunits=simplekml.Units.insetpixels)

    overlaytext=''
    total_scale=1.0
    for r in range(4,res+1):
        try:
            overlaytext+='R'+str(r)+' '+str(round(scale[r]['scale'],3))+'|'
            total_scale=total_scale*scale[r]['scale']
        except KeyError:
            pass

    if overlaytext=='':
        overlaytext='R'+str(res)
    else:
        overlaytext+='Scale '+str(round(total_scale,3))
    # cannot figure out how to just put text so this is silly but generate image from text
    #osd.icon.href='http://chart.apis.google.com/chart?chst=d_text_outline&chld=FFBBBB|16|h|BB0000|b|'+'R'+str(res)+' '+'R'+str(res+1)
    osd.icon.href='http://chart.apis.google.com/chart?chst=d_text_outline&chld=FFBBBB|16|h|BB0000|b|'+overlaytext
        
    return kml.kml()

class S(BaseHTTPRequestHandler):
    def _set_response(self):
        print('set response')
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        

    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response()

        # didn't try to figure out why these character are here before alt
        try:
            bbox,alt=self.path.split('CAMERA=%5C%0A%20%20%20%20%20%20')
            west,south,east,north=bbox.split(',')
            north=north.strip(';')
            garbage,west=west.split('=')
        except ValueError:
            return


        # find the center of the map and the altitude
        bbox = bbox.split(',')
        west = float(west)
        south = float(south)
        east = float(east)
        north = float(north)
        lng = ((east - west) / 2) + west
        lat = ((north - south) / 2) + south
        polykml=geth3polys(lng,lat,float(alt))

        # send the new kml back to google earth
        self.wfile.write(polykml.encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself

        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), post_data.decode('utf-8'))

        #self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

def run(server_class=HTTPServer, handler_class=S, port=8001):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')

if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
