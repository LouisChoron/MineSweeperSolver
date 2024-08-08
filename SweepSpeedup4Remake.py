import webbrowser
import pyautogui
import numpy as np
import random
import time
from pyscreeze import ImageNotFoundException
import cProfile

np.set_printoptions(linewidth=150)

# Open Minesweeper
webbrowser.open("https://minesweeperonline.com/", new=0, autoraise=True)

# Pixel Info
# TL  574, 304
# TR  1293  304
# BL  574  687   (1 square width 24),    30 x 16 squares
# BR  1293  687

# Click Functions
def click(a, b):
    pyautogui.click(a, b)
def right_click(a,b):
    pyautogui.click(a,b,button='right')
    
# Let's say, as cannot find half of 24 pixels etc, that 12th is middle
Grid = np.zeros([16, 30], dtype = int)         # Grid will hold VALUES
Centres = np.zeros([16, 30], dtype = 'd,d')    # Centres will hold POSITIONS
mid_top_left=(586,316)

dtype = np.dtype([('x_range', '2f8'), ('y_range', '2f8')])
Ranges = np.zeros([16,30], dtype= dtype)       # Ranges will hold ((x1,x2),(y1,y2)) each square RANGES

# Fill positions and ranges
def fill_Centres(X_amount=16, Y_amount=30, start_x=mid_top_left[0], start_y=mid_top_left[1], increment=24):   
    for i in range(X_amount):
        for j in range(Y_amount):
            Centres[i, j][0] = start_x + j * increment
            Centres[i, j][1] = start_y + i * increment

def fill_Ranges(X_amount=16, Y_amount=30, start_x=574, start_y=304, increment=24):
    lim1_y=start_y
    for i in range(X_amount):
        lim1_x=start_x
        
        # Y stuff
        lim2_y=lim1_y+(increment-1)
    
        for j in range(Y_amount):
            # X stuff
            lim2_x=lim1_x+(increment-1)
            Ranges[i,j][0][0]=lim1_x
            Ranges[i,j][0][1]=lim2_x
            lim1_x=lim2_x+1
            
            # Y stuff
            Ranges[i,j][1][0]=lim1_y
            Ranges[i,j][1][1]=lim2_y
        lim1_y=lim2_y+1
            
fill_Centres()    
fill_Ranges()

# Pause to let screen load
time.sleep(3)

# Pick a random starting location
def random_click():
    random_location = Centres[random.randint(0, Centres.shape[0] - 1), random.randint(0, Centres.shape[1] - 1)]
    click(random_location[0],random_location[1])
    
random_click()

# Given a point, finds location in RANGES and adds value to index in GRID
def update_grid_with_point(x, y, value):
    x_ranges = Ranges['x_range']
    y_ranges = Ranges['y_range']
    
    # Create masks for x and y ranges
    x_mask = np.logical_and(x_ranges[:, :, 0] <= x, x <= x_ranges[:, :, 1])
    y_mask = np.logical_and(y_ranges[:, :, 0] <= y, y <= y_ranges[:, :, 1])
    
    # Combine masks
    mask = np.logical_and(x_mask, y_mask)
    
    # Find indices where mask is True and update Grid
    if np.any(mask):
        i, j = np.where(mask)
        Grid[i[0], j[0]] = value
        return True
    
    return False

# Given the image of a number, finds locations of that number/image on screen, then updates python GRID with it
def locate_image_and_update(image_path, region, value):
    try:
        locs=pyautogui.locateAllOnScreen(image_path, region=region, confidence=0.8, grayscale=True)  #confidence needed to improve accuracy
        for pos in locs:
            update_grid_with_point(pos[0],pos[1],value)
    except ImageNotFoundException:
        #print("Image not found. Returning None.")
        return None
    except Exception as e:
        print(f"An error occurred: {str(e)}. Returning None.")
        return None

# Define the region (minesweeper screen)
region = (574, 304, 719, 383)

# Locate all numbers + update GRID
def update_numbers():
    SIX_locs = locate_image_and_update('Acer Computer\Summer 2024\Sweep_images\Six.png', region, 6)
    UNKNOWN_locs = locate_image_and_update(r'Acer Computer\Summer 2024\Sweep_images\Unknown.png', region, 0)
    EMPTY_locs = locate_image_and_update('Acer Computer\Summer 2024\Sweep_images\Empty.png', region, -2) 
    ONE_locs = locate_image_and_update('Acer Computer\Summer 2024\Sweep_images\One.png', region, 1)
    TWO_locs = locate_image_and_update('Acer Computer\Summer 2024\Sweep_images\Two.png', region, 2)
    THREE_locs = locate_image_and_update('Acer Computer\Summer 2024\Sweep_images\Three.png', region, 3)
    FOUR_locs = locate_image_and_update('Acer Computer\Summer 2024\Sweep_images\Four.png', region, 4)
    FIVE_locs = locate_image_and_update('Acer Computer\Summer 2024\Sweep_images\Five.png', region, 5)
    FLAG_locs = locate_image_and_update('Acer Computer\Summer 2024\Sweep_images\Flag.png', region, -1) # KEEP LAST(?)

update_numbers()

print("####################")

# Get the shape of the grid
rows, cols = Grid.shape

############################################################################ Two main functions

def identify_bombs_around():
    '''If number X touches ONLY X unknowns (and no flags/bomb), right click them all as bombs'''
    
    # Define directions for neighbors (top, bottom, left, right, diagonal)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    
    # Initialize changed flag
    changed = False
    
    # Iterate over each element in the Grid
    for i in range(rows):  # Rows
        for j in range(cols):  # Columns
            
            # If current element is 1
            if Grid[i, j] == 1:  
                # Check if there's already a neighboring -1
                has_negative_one_neighbor = False
                for di, dj in directions:
                    ni, nj = i + di, j + dj
                    # Check bounds
                    if 0 <= ni < rows and 0 <= nj < cols:
                        # If neighbor is -1, set flag and break
                        if Grid[ni, nj] == -1:
                            has_negative_one_neighbor = True
                            break
                
                # If there's no neighboring -1, check for a neighboring 0
                if not has_negative_one_neighbor:
                    zero_count = 0
                    for di, dj in directions:
                        ni, nj = i + di, j + dj
                        # Check bounds
                        if 0 <= ni < rows and 0 <= nj < cols:
                            # If neighbor is 0, increment zero_count
                            if Grid[ni, nj] == 0:
                                zero_count += 1
                    
                    # If exactly one neighboring zero, change it to -1
                    if zero_count == 1:
                        for di, dj in directions:
                            ni, nj = i + di, j + dj
                            if 0 <= ni < rows and 0 <= nj < cols:
                                if Grid[ni, nj] == 0:
                                    Grid[ni, nj] = -1
                                    # Add flags
                                    x, y = Centres[ni, nj]
                                    right_click(x, y)  
                                    changed = True  # Set changed flag 
                
            # If current element is 2
            elif Grid[i, j] == 2:
                # Count the number of flags (-1) and empty spaces (0) around the 2
                flag_count = 0
                zero_count = 0
                zero_positions = []

                for di, dj in directions:
                    ni, nj = i + di, j + dj
                    # Check bounds
                    if 0 <= ni < rows and 0 <= nj < cols:
                        if Grid[ni, nj] == -1:
                            flag_count += 1
                        elif Grid[ni, nj] == 0:
                            zero_count += 1
                            zero_positions.append((ni, nj))
                
                # If there are no flags and exactly two empty spaces, flag both
                if flag_count == 0 and zero_count == 2:
                    for ni, nj in zero_positions:
                        Grid[ni, nj] = -1
                        x, y = Centres[ni, nj]
                        right_click(x, y)
                        changed = True

                # If there is one flag and one empty space, flag that empty space
                elif flag_count == 1 and zero_count == 1:
                    ni, nj = zero_positions[0]
                    Grid[ni, nj] = -1
                    x, y = Centres[ni, nj]
                    right_click(x, y)
                    changed = True
            
            # If current element is 3
            elif Grid[i, j] == 3:  
                zero_count = 0
                flag_count = 0
                zero_positions = []
                
                for di, dj in directions:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < rows and 0 <= nj < cols:
                        if Grid[ni, nj] == 0:
                            zero_count += 1
                            zero_positions.append((ni, nj))
                        elif Grid[ni, nj] == -1:
                            flag_count += 1
                
                # If there are no flags and exactly three unknowns, or one flag and two unknowns, or two flags and one unknown
                if (flag_count == 0 and zero_count == 3) or (flag_count == 1 and zero_count == 2) or (flag_count == 2 and zero_count == 1):
                    for ni, nj in zero_positions:
                        Grid[ni, nj] = -1
                        x, y = Centres[ni, nj]
                        right_click(x, y)
                        changed = True
            
            # If current element is 4
            elif Grid[i, j] == 4:  
                # Count the number of neighboring -1s and 0s
                flag_count = 0
                zero_count = 0
                for di, dj in directions:
                    ni, nj = i + di, j + dj
                    # Check bounds
                    if 0 <= ni < rows and 0 <= nj < cols:
                        if Grid[ni, nj] == -1:
                            flag_count += 1
                        elif Grid[ni, nj] == 0:
                            zero_count += 1
                
                # Flag unknowns based on the number of flags and unknowns
                if (flag_count == 0 and zero_count == 4) or \
                   (flag_count == 1 and zero_count == 3) or \
                   (flag_count == 2 and zero_count == 2) or \
                   (flag_count == 3 and zero_count == 1):
                    for di, dj in directions:
                        ni, nj = i + di, j + dj
                        if 0 <= ni < rows and 0 <= nj < cols and Grid[ni, nj] == 0:
                            Grid[ni, nj] = -1
                            x, y = Centres[ni, nj]
                            right_click(x, y)
                            changed = True
            
            # If current element is 5
            elif Grid[i, j] == 5:  
                # Count the number of neighboring -1s and 0s
                flag_count = 0
                zero_count = 0
                for di, dj in directions:
                    ni, nj = i + di, j + dj
                    # Check bounds
                    if 0 <= ni < rows and 0 <= nj < cols:
                        if Grid[ni, nj] == -1:
                            flag_count += 1
                        elif Grid[ni, nj] == 0:
                            zero_count += 1
                            
                # Flag unknowns based on the number of flags and unknowns
                if (flag_count == 0 and zero_count == 5) or \
                   (flag_count == 1 and zero_count == 4) or \
                   (flag_count == 2 and zero_count == 3) or \
                   (flag_count == 3 and zero_count == 2) or \
                   (flag_count == 4 and zero_count == 1):
                    for di, dj in directions:
                        ni, nj = i + di, j + dj
                        if 0 <= ni < rows and 0 <= nj < cols and Grid[ni, nj] == 0:
                            Grid[ni, nj] = -1
                            x, y = Centres[ni, nj]
                            right_click(x, y)
                            changed = True
            
            # If current element is 6
            elif Grid[i, j] == 6:  
                # Count the number of neighboring -1s and 0s
                flag_count = 0
                zero_count = 0
                for di, dj in directions:
                    ni, nj = i + di, j + dj
                    # Check bounds
                    if 0 <= ni < rows and 0 <= nj < cols:
                        if Grid[ni, nj] == -1:
                            flag_count += 1
                        elif Grid[ni, nj] == 0:
                            zero_count += 1
                
                # Flag unknowns based on the number of flags and unknowns
                if (flag_count == 0 and zero_count == 6) or \
                   (flag_count == 1 and zero_count == 5) or \
                   (flag_count == 2 and zero_count == 4) or \
                   (flag_count == 3 and zero_count == 3) or \
                   (flag_count == 4 and zero_count == 2) or \
                   (flag_count == 5 and zero_count == 1):
                    for di, dj in directions:
                        ni, nj = i + di, j + dj
                        if 0 <= ni < rows and 0 <= nj < cols and Grid[ni, nj] == 0:
                            Grid[ni, nj] = -1
                            x, y = Centres[ni, nj]
                            right_click(x, y)
                            changed = True
                                                                        
    return changed

def flag_click():
    '''If number X already touches X flags/bombs, click all other unknowns'''
    
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    # Initialize changed flag (to allow for looping until no change)
    changed = False
    
    # Iterate through the grid to find elements equal to 1
    for i in range(rows):
        for j in range(cols):
            
            # If current element is 1
            if Grid[i, j] == 1:
                # Check neighbors for -1 and change neighbors of the original 1 which are 0 to 9
                for di in [-1, 0, 1]:  # relative row indices for neighbors
                    for dj in [-1, 0, 1]:  # relative column indices for neighbors
                        if di == 0 and dj == 0:
                            continue  # skip the element itself
                        ni, nj = i + di, j + dj  # neighbor indices
                        if 0 <= ni < rows and 0 <= nj < cols:  # ensure within bounds
                            if Grid[ni, nj] == -1:
                                # Change neighbors of the original 1 which are 0 to 9 in the modified grid
                                for di2 in [-1, 0, 1]:
                                    for dj2 in [-1, 0, 1]:
                                        nni, nnj = i + di2, j + dj2
                                        if 0 <= nni < rows and 0 <= nnj < cols:
                                            if Grid[nni, nnj] == 0:
                                                Grid[nni, nnj] = 9
                                                # Click unknowns
                                                x, y = Centres[nni, nnj]
                                                click(x,y)
                                                changed = True  # Set changed flag  
            
            # If current element is 2
            elif Grid[i, j] == 2:
                flag_count = 0
                unknown_positions = []
                
                for di, dj in directions:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < rows and 0 <= nj < cols:
                        if Grid[ni, nj] == -1:
                            flag_count += 1
                        elif Grid[ni, nj] == 0:
                            unknown_positions.append((ni, nj))
                
                # If there are exactly two flags, click all other unknowns
                if flag_count == 2:
                    for ni, nj in unknown_positions:
                        Grid[ni, nj] = 9  # Mark as clicked
                        x, y = Centres[ni, nj]
                        click(x, y)
                        changed = True
            
            # If current element is 3 
            elif Grid[i, j] == 3:  # If current element is 3
                flag_count = 0
                unknown_positions = []
                
                for di, dj in directions:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < rows and 0 <= nj < cols:
                        if Grid[ni, nj] == -1:
                            flag_count += 1
                        elif Grid[ni, nj] == 0:
                            unknown_positions.append((ni, nj))
                
                # If there are exactly three flags, click all other unknowns
                if flag_count == 3:
                    for ni, nj in unknown_positions:
                        Grid[ni, nj] = 9  # Mark as clicked
                        x, y = Centres[ni, nj]
                        click(x, y)
                        changed = True
            
            # If current element is 4         
            elif Grid[i, j] == 4:
                flag_count = 0
                for di, dj in directions:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < rows and 0 <= nj < cols and Grid[ni, nj] == -1:
                        flag_count += 1
                
                if flag_count == 4:
                    for di, dj in directions:
                        ni, nj = i + di, j + dj
                        if 0 <= ni < rows and 0 <= nj < cols and Grid[ni, nj] == 0:
                            Grid[ni, nj] = 9  # Marking it as visited (if needed)
                            x, y = Centres[ni, nj]
                            click(x, y)
                            changed = True

            # If current element is 5
            elif Grid[i, j] == 5:
                flag_count = 0
                for di, dj in directions:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < rows and 0 <= nj < cols and Grid[ni, nj] == -1:
                        flag_count += 1
                
                if flag_count == 5:
                    for di, dj in directions:
                        ni, nj = i + di, j + dj
                        if 0 <= ni < rows and 0 <= nj < cols and Grid[ni, nj] == 0:
                            Grid[ni, nj] = 9  # Marking it as visited (if needed)
                            x, y = Centres[ni, nj]
                            click(x, y)
                            changed = True
            
            # If current element is 6         
            elif Grid[i, j] == 6:
                flag_count = 0
                for di, dj in directions:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < rows and 0 <= nj < cols and Grid[ni, nj] == -1:
                        flag_count += 1
                
                if flag_count == 6:
                    for di, dj in directions:
                        ni, nj = i + di, j + dj
                        if 0 <= ni < rows and 0 <= nj < cols and Grid[ni, nj] == 0:
                            Grid[ni, nj] = 9  # Marking it as visited (if needed)
                            x, y = Centres[ni, nj]
                            click(x, y)
                            changed = True
            
    return changed

############################################################################ 2's

def flag_121_pattern():
    '''1-2-1 minesweeper pattern, even if one flag already placed (4 orientations)'''
    changed = False
    rows, cols = Grid.shape
    
    # Check horizontal 1-2-1 pattern with zeros above and below
    for i in range(1, rows - 1):
        for j in range(1, cols - 2):
            if (Grid[i, j] == 1 and Grid[i, j+1] == 2 and Grid[i, j+2] == 1 and
                (Grid[i-1, j] == 0 or Grid[i-1, j] == -1) and 
                Grid[i-1, j+1] == 0 and 
                (Grid[i-1, j+2] == 0 or Grid[i-1, j+2] == -1) and
                #Grid[i+1, j] == -2 and Grid[i+1, j+1] == -2 and Grid[i+1, j+2] == -2):
                (Grid[i+1, j] != -1 and Grid[i+1, j] != 0) and (Grid[i+1, j+1] != -1 and Grid[i+1, j+1] != 0) and 
                (Grid[i+1, j+2] != -1 and Grid[i+1,j+2] != 0)): #unknowns above, almost anything below
                
                # Flag the unknown cells above the 1's if they are not already flagged
                if Grid[i-1, j] == 0:
                    Grid[i-1, j] = -1
                    x1, y1 = Centres[i-1, j]
                    right_click(x1, y1)

                if Grid[i-1, j+2] == 0:
                    Grid[i-1, j+2] = -1
                    x2, y2 = Centres[i-1, j+2]
                    right_click(x2, y2)
                
                # Click the space between the flags
                Grid[i-1, j+1] = 9
                x3, y3 = Centres[i-1, j+1]
                click(x3, y3)

                changed = True
            
            # Check horizontal 1-2-1 pattern with zeros below and above
            if (Grid[i, j] == 1 and Grid[i, j+1] == 2 and Grid[i, j+2] == 1 and
                (Grid[i+1, j] == 0 or Grid[i+1, j] == -1) and 
                Grid[i+1, j+1] == 0 and 
                (Grid[i+1, j+2] == 0 or Grid[i+1, j+2] == -1) and
                #Grid[i-1, j] == -2 and Grid[i-1, j+1] == -2 and Grid[i-1, j+2] == -2):
                (Grid[i-1, j] != -1 and Grid[i-1, j] != 0) and (Grid[i-1, j+1] != -1 and Grid[i-1, j+1] != 0) and 
                (Grid[i-1, j+2] != -1 and Grid[i-1,j+2] != 0)):
                
                # Flag the unknown cells below the 1's if they are not already flagged
                if Grid[i+1, j] == 0:
                    Grid[i+1, j] = -1
                    x1, y1 = Centres[i+1, j]
                    right_click(x1, y1)

                if Grid[i+1, j+2] == 0:
                    Grid[i+1, j+2] = -1
                    x2, y2 = Centres[i+1, j+2]
                    right_click(x2, y2)
                
                # Click the space between the flags
                Grid[i+1, j+1] = 9
                x3, y3 = Centres[i+1, j+1]
                click(x3, y3)

                changed = True
                
    # Check vertical 1-2-1 pattern with zeros left and right
    for i in range(1, rows - 2):
        for j in range(1, cols - 1):
            if (Grid[i, j] == 1 and Grid[i+1, j] == 2 and Grid[i+2, j] == 1 and
                (Grid[i, j-1] == 0 or Grid[i, j-1] == -1) and 
                Grid[i+1, j-1] == 0 and 
                (Grid[i+2, j-1] == 0 or Grid[i+2, j-1] == -1) and
                #Grid[i, j+1] == -2 and Grid[i+1, j+1] == -2 and Grid[i+2, j+1] == -2):
                (Grid[i, j+1] != -1 and Grid[i, j+1] != 0) and (Grid[i+1, j+1] != -1 and Grid[i+1, j+1] != 0) and 
                (Grid[i+2, j+1] != -1 and Grid[i+2,j+1] != 0)):
                
                # Flag the unknown cells left of the 1's if they are not already flagged
                if Grid[i, j-1] == 0:
                    Grid[i, j-1] = -1
                    x1, y1 = Centres[i, j-1]
                    right_click(x1, y1)

                if Grid[i+2, j-1] == 0:
                    Grid[i+2, j-1] = -1
                    x2, y2 = Centres[i+2, j-1]
                    right_click(x2, y2)
                
                # Click the space between the flags
                Grid[i+1, j-1] = 9
                x3, y3 = Centres[i+1, j-1]
                click(x3, y3)

                changed = True
            
            # Check vertical 1-2-1 pattern with zeros right and left
            if (Grid[i, j] == 1 and Grid[i+1, j] == 2 and Grid[i+2, j] == 1 and
                (Grid[i, j+1] == 0 or Grid[i, j+1] == -1) and 
                Grid[i+1, j+1] == 0 and 
                (Grid[i+2, j+1] == 0 or Grid[i+2, j+1] == -1) and
                #Grid[i, j-1] == -2 and Grid[i+1, j-1] == -2 and Grid[i+2, j-1] == -2):
                (Grid[i, j-1] != -1 and Grid[i, j-1] != 0) and (Grid[i+1, j-1] != -1 and Grid[i+1, j-1] != 0) and 
                (Grid[i+2, j-1] != -1 and Grid[i+2,j-1] != 0)):
                
                # Flag the unknown cells right of the 1's if they are not already flagged
                if Grid[i, j+1] == 0:
                    Grid[i, j+1] = -1
                    x1, y1 = Centres[i, j+1]
                    right_click(x1, y1)

                if Grid[i+2, j+1] == 0:
                    Grid[i+2, j+1] = -1
                    x2, y2 = Centres[i+2, j+1]
                    right_click(x2, y2)
                
                # Click the space between the flags
                Grid[i+1, j+1] = 9
                x3, y3 = Centres[i+1, j+1]
                click(x3, y3)

                changed = True
    
    return changed


def flag_1221_pattern():
    '''1-2-2-1 minesweeper pattern (only one orientation here, tbd)'''
    changed = False
    for i in range(1, rows - 1):
        for j in range(1, cols - 3):
            # Check for the 1-2-2-1 pattern with -2's below and 0 (or -1) above the 2's
            if (Grid[i, j] == 1 and Grid[i, j+1] == 2 and Grid[i, j+2] == 2 and Grid[i, j+3] == 1 and
                Grid[i-1, j] == 0 and (Grid[i-1, j+1] == 0 or Grid[i-1, j+1] == -1) and 
                (Grid[i-1, j+2] == 0 or Grid[i-1, j+2] == -1) and Grid[i-1, j+3] == 0 and
                Grid[i+1, j] == -2 and Grid[i+1, j+1] == -2 and Grid[i+1, j+2] == -2 and Grid[i+1, j+3] == -2):

                # Flag the cells above the 2's only if they are 0 or already flagged
                if Grid[i-1, j+1] == 0:
                    Grid[i-1, j+1] = -1
                    x, y = Centres[i-1, j+1]
                    right_click(x, y)
                    changed = True
                if Grid[i-1, j+2] == 0:
                    Grid[i-1, j+2] = -1
                    x, y = Centres[i-1, j+2]
                    right_click(x, y)
                    changed = True

                # Left-click the cells above the 1's if they are unknown (0)
                if Grid[i-1, j] == 0:
                    Grid[i-1, j] = 9
                    x, y = Centres[i-1, j]
                    click(x, y)
                    changed = True
                if Grid[i-1, j+3] == 0:
                    Grid[i-1, j+3] = 9
                    x, y = Centres[i-1, j+3]
                    click(x, y)
                    changed = True

    return changed

############################################################################ Overall

def Minesweep():
    '''Run until no more changes are made'''
    while True:
        changed = False
        
        # Process numbers until no changes are made
        changed_ID = identify_bombs_around()
        changed_Flag = flag_click()     
        if changed_ID or changed_Flag:
            changed = True
            update_numbers()
            
        # Process 1-2-1 once
        changed_121 = flag_121_pattern()
        if changed_121:
            changed = True
            update_numbers()
            
        # Process 1-2-2-1 once
        changed_1221 = flag_1221_pattern()
        if changed_1221:
            changed = True
            update_numbers()

        # Such that we can also stop if hit bomb
        try:
            if not changed or pyautogui.locateOnScreen('Acer Computer\Summer 2024\Sweep_images\Bomb.png',region=region, confidence=0.8, grayscale=True) is not None:
                message = pyautogui.confirm(text='Stuck!', title='End of Game', buttons=['OK', 'Restart'])
                if message == 'OK':
                    return  # Exit the Minesweep function
                else:
                    click(935,265)
                    random_click()
                    update_numbers()
                    Minesweep()
        except pyautogui.ImageNotFoundException:
            pass
        
Minesweep()
#cProfile.run('Minesweep()')