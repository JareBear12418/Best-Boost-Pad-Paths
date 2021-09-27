from numpy.lib.function_base import _calculate_shapes, _sinc_dispatcher
import boost_pad_loc
import numpy as np
import cv2
import random
from utility.vec import Vec3 as vec
import math
import time

BOOST_PAD_LOCATIONS = boost_pad_loc.BOOST_PAD_LOCATIONS
# img = cv2.imread('watch.jpg',cv2.IMREAD_COLOR)

# ball_position = vec(x=1478,y=979,z=0)
# player_position = vec(x=5916,y=8702,z=0)
ball_position = vec(x=random.randint(0,8192),y=random.randint(0,10240),z=0)
player_position = vec(x=random.randint(0,8192),y=random.randint(0,10240),z=0)
print(ball_position, player_position)

img = np.zeros((10240, 8192, 3), dtype = "uint8")
# cv2.line(img,(0,0),(200,300),(255,255,255),50)
# cv2.rectangle(img,(500,250),(1000,500),(0,0,255),15)
def fix_origin():
    '''
    Because Rocket League's map origin is at the center,
    we need to offset everything to map everything properly.
    
    cv2's origin is top left, so we need to account for that.
    '''
    for index, boost_pad in enumerate(BOOST_PAD_LOCATIONS):
        x: int = boost_pad[0]
        y: int = boost_pad[1]
        if x >= 0:
            x = (8192/2) + abs(x)
        elif x < 0:
            x = (8192/2) - abs(x)
        if y >= 0:
            y = (10240/2) + abs(y)
        elif y < 0:
            y = (10240/2) - abs(y)
        BOOST_PAD_LOCATIONS[index][0] = x
        BOOST_PAD_LOCATIONS[index][1] = y
    
fix_origin()

def correct_origin(x: int, y: int) -> int:
    '''
    Converts Unreal coordinates to Opencv Coordinates
    '''
    if x >= 0:
        x = (8192/2) + abs(x)
    elif x < 0:
        x = (8192/2) - abs(x)
    if y >= 0:
        y = (10240/2) + abs(y)
    elif y < 0:
        y = (10240/2) - abs(y)
    return x, y

def draw_ball(pos: vec, img: np.zeros) -> cv2.circle:
    return(cv2.circle(img,(int(pos.x), int(pos.y)), 300, (255,255,255), -1))

def draw_player(pos: vec, is_blue_team: bool, img: np.zeros) -> cv2.rectangle:
    '''
    Origin is center
    '''
    w = 400
    h = 250
    return (cv2.rectangle(img,(int(pos.x-(w/2)),int(pos.y-(h/2))),(int(pos.x+(w/2)), int(pos.y+(h/2))),(255 if is_blue_team else 0,128 if not is_blue_team else 0, 255 if not is_blue_team else 0),15))

def draw_boosts(img: np.zeros):
    for i, boost_pad in enumerate(BOOST_PAD_LOCATIONS):
        x: int = boost_pad[0]
        y: int = boost_pad[1]

        cv2.putText(img, str(i), (int(x), int(y-10)), cv2.FONT_HERSHEY_SIMPLEX, 10, (36,255,12), 2)
        BIG_BOOST: bool = boost_pad[2] == 73.0
        if BIG_BOOST:
            img = cv2.circle(img,(int(x), int(y)), 208, (0,160,255), -1)
        else:
            img = cv2.circle(img,(int(x), int(y)), 144, (0,128,255), -1)
    return img

def get_vec_list(player_pos: vec, ball_pos: vec, boost_pads_loc: list[vec]) -> list:
    '''
    Combine all ball,player,boosts locations into one list as Vectors.
    '''
    vector_list = []
    # vector_list.append(player_pos)
    for boost_pad in boost_pads_loc:
        vector_list.append(vec(boost_pad[0], boost_pad[1], 0))
    vector_list.append(ball_pos)
    return vector_list

def calculate_shortest_distance(points) -> list:
    start_time = time.process_time()
    start: vec = player_position
    end: vec = ball_position
    shortest_path_points: list[vec] = []
    max_dist: float = math.hypot(end.x - start.x, end.y - start.y)
    TOTAL_LENGTH: float = math.hypot(end.x - start.x, end.y - start.y)
    distances_length: list[float] = []
    closest_vector: vec = None
    index_of_vector: int = 0
    shortest_distance: float = float("inf")
    cv2.circle(img,(int(end.x),int(end.y)),int(max_dist),(0,0,255), thickness=10)
    found_best_path: bool = False
    loops: int = 0
    def remove_outside_points(max_dist: float):
        '''
        remove points if they are outside the 'red' circle
        '''
        for i, point in enumerate(points):
            d2 = math.hypot(end.x - point.x, end.y - point.y)
            if d2 > max_dist:
                points.pop(i)
    while not found_best_path:
        shortest_distance = float('inf')
        remove_outside_points(max_dist)
        
        print(len(points))
        for i, point in enumerate(points):
            if loops == 0:
                # distance from preveious point to next possible point
                d1 = math.hypot(point.x - start.x, point.y - start.y)
                # distance from point to end.
                d2 = math.hypot(end.x - point.x, end.y - point.y)
            else:
                try:
                    # distance from preveious point to next possible point
                    d1 = math.hypot(point.x - last_vector.x, point.y - last_vector.y)
                    # distance from point to end.
                    d2 = math.hypot(end.x - point.x, end.y - point.y)
                except IndexError:
                    break
            if ((d1-200) <= shortest_distance or (d1+200) <= shortest_distance) and d2+500 <= max_dist-500:
                shortest_distance = d1
                closest_vector = point
                index_of_vector = i if loops == 0 else i+1
                
        if shortest_distance == float('inf'): 
            found_best_path = True
        distances_length.append(shortest_distance)
        shortest_path_points.append(closest_vector)
        max_dist = math.hypot(end.x - closest_vector.x, end.y - closest_vector.y)
        cv2.circle(img,(int(end.x),int(end.y)),int(max_dist),(0,0,255), thickness=10)
        last_vector = closest_vector
        try:
            points.pop(index_of_vector)
            remove_outside_points(max_dist)
        except IndexError: 
            break
        loops += 1
    
    print(f'{sum(distances_length)}<{TOTAL_LENGTH}')
    print(time.process_time() - start_time)
    return shortest_path_points
  
if __name__ == '__main__':
    draw_boosts(img=img)
    draw_ball(pos=ball_position, img=img)
    draw_player(pos=player_position, is_blue_team=True, img=img)
    points = get_vec_list(player_pos=player_position, ball_pos=ball_position,boost_pads_loc=BOOST_PAD_LOCATIONS)
    quickest_points = calculate_shortest_distance(points)
    cv2.line(img, (int(player_position.x), int(player_position.y)), (int(quickest_points[0].x), int(quickest_points[0].y)), (0, 255, 0), thickness=2)
    for i, point in enumerate(quickest_points):
        try:
            cv2.line(img, (int(point.x), int(point.y)), (int(quickest_points[i+1].x), int(quickest_points[i+1].y)), (0, 255, 0), thickness=2)
        except IndexError:
            cv2.line(img, (int(point.x), int(point.y)), (int(ball_position.x), int(ball_position.y)), (0, 255, 0), thickness=10)
            
    cv2.imwrite("out.png", img)
    
    print('done')