import os
import datetime
import time
import urllib.request
import xml.dom.minidom as minidom

from PIL import Image

TIMEOUT = 10.0

TZ_OFFSET_HOURS = 3

URL_MAP_TILE = 'https://meteoinfo.ru/hmc-output/osm_lr/8/{0}/{1}.png'
URL_NOWCAST = 'https://meteoinfo.ru/hmc-output/nowcast3/nowcast.php'
URL_NOWCAST_TILE = 'https://meteoinfo.ru/res/nowcast/0/ncgi.php?' + \
                   'tnz=8&tnx={0}&tny={1}' + \
                   '&inidt={2}' + \
                   '&time={3}' + \
                   '&service=WMS&request=GetMap&layers=1' + \
                   '&styles=&transparent=true&version=1.1.1&height=256&width=256'

IMAGES_DIR = './imgs'

MAP_TNX = 154
MAP_TNYS = [79, 80]
NC_MAP_TNYS = [175, 176]

B_BOX = [146, 213, 90, 110]

VALUE_PCT_THRESHOLD = 5

def main_test():
    print('Testing: downloading images...')

    downloaded, num_times = download_nowcast_data()

    if downloaded:
        download_map_images()
    
        print('Testing: Processing images...')
        image_values = process_nowcast_images(176, 175, num_times)
        print(image_values)
        
        print('Testing: Success')
    else:
        print('Testing: Fail')
        
def get_info():
    """ Get nowcast info """
    
    # Download nowcast data
    downloaded, num_times = download_nowcast_data()

    if downloaded:
        try:
            image_values = process_nowcast_images(176, 175, num_times)
        except:
            return None
        
        # Process values into time and event
        going_now = image_values[0] > VALUE_PCT_THRESHOLD
        
        total_time = 0
        changing = False
        
        for val in image_values[1:]:
            total_time += 10
            is_going = val > VALUE_PCT_THRESHOLD
            if is_going != going_now:
                changing = True
                break
        
        return {
            'raw': str(image_values),
            'info': {
                'minutes': total_time,
                'going': going_now,
                'starting': not going_now and changing,
                'ending': going_now and changing
            }
        }
    else:
        return None
        
def download_nowcast_data():
    """ Download time extents and nowcast tiles """

    extent_info = download_nowcast_time_extent()
    
    if extent_info is not None:
        init_time, all_times = extent_info
        
        remove_old_images()
        download_nowcast_images(init_time, all_times)
        
        return (True, len(all_times))
    else:
        return (False, None)
        
def download_nowcast_time_extent():
    """ Download nowcast times """

    nc_request = urllib.request.Request(URL_NOWCAST, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Connection': 'close',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
        'Referer': 'https://meteoinfo.ru/nowcasting'
    })

    resp = urllib.request.urlopen(nc_request)
    
    if resp.status == 200:
        nc_doc = minidom.parse(resp)
        resp.close()
        
        time_extent_node = nc_doc.getElementsByTagName('Extent')[0]
        init_time = time_extent_node.attributes['default'].value
        all_times = time_extent_node.firstChild.nodeValue.split(',')
        
        return (init_time, all_times)
    else:
        return None
    
def remove_old_images():
    """ Remove all temporary downloaded images """

    for img_file_name in os.listdir(IMAGES_DIR):
        if img_file_name.endswith('.png'):
            os.unlink(os.path.join(IMAGES_DIR, img_file_name))

def download_map_images():
    """ Download images from map layer """

    for tny in MAP_TNYS:
        tile_request_url = URL_MAP_TILE.format(MAP_TNX, tny)
        with urllib.request.urlopen(tile_request_url) as tile_resp:
            with open('{0}/map_{1}.png'.format(IMAGES_DIR, tny), 'wb') as out_file:
                out_file.write(tile_resp.read())
                
def download_nowcast_images(init_time, all_times):
    """ Download images from nowcast layer for given times """
    import time
       
    init_dt = datetime.datetime.strptime(init_time, '%Y-%m-%dT%H:%M:%S.%fZ')
    local_init_dt = init_dt + datetime.timedelta(hours=TZ_OFFSET_HOURS)
    ts = time.mktime(local_init_dt.timetuple())
    local_init_dt_ts = int(ts) * 1000
    
    ti = 0

    for time in all_times:
        for tny in NC_MAP_TNYS:
            nc_tile_url = URL_NOWCAST_TILE.format(MAP_TNX, tny, local_init_dt_ts, time)
            
            with urllib.request.urlopen(nc_tile_url) as tile_resp:
                with open('./imgs/nc_{0}_{1}.png'.format(tny, ti), 'wb') as out_file:
                    out_file.write(tile_resp.read())
                
        ti += 1
        
def process_nowcast_images(top_y, bottom_y, num_images):
    """ Process nowcast images' pixels """

    image_values = list()
    max_value = B_BOX[2] * B_BOX[3]

    for n in range(0, num_images):
        with Image.open(get_image_path(top_y, n)) as top_tile:
            with Image.open(get_image_path(bottom_y, n)) as bottom_tile:
                size = top_tile.size[0]
                canvas_size = (size, size * 2)
                back = Image.new('RGBA', canvas_size)
            
                back.paste(top_tile, (0, 0))
                back.paste(bottom_tile, (0, size))
            
                gray_image = back.convert('L')

                value = 0
                for x in range(B_BOX[0], B_BOX[0] + B_BOX[2]):
                     for y in range(B_BOX[1], B_BOX[1] + B_BOX[3]):
                         p = 255 - gray_image.getpixel((x, y))
                         value += 1 if p > 15 else 0
            
                value_pct = int(value * 100 / max_value)
                image_values.append(value_pct)
              
    return image_values

def get_image_path(y, n):
    """ Get full path to nowcast image file """

    return os.path.join(IMAGES_DIR, 'nc_{0}_{1}.png'.format(y, n))

if __name__ == '__main__':
    print(get_info())
