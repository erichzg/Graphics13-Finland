import mdl
from display import *
from matrix import *
from draw import *

"""======== first_pass( commands, symbols ) ==========

  Checks the commands array for any animation commands
  (frames, basename, vary)

  Should set num_frames and basename if the frames
  or basename commands are present

  If vary is found, but frames is not, the entire
  program should exit.

  If frames is found, but basename is not, set name
  to some default value, and print out a message
  with the name being used.
  ==================== """
def first_pass( commands ):
    frames_present = vary_present = basename_present = False
    num_frames = 1
    for command in commands:
        c = command['op']
        if c == 'frames':
            num_frames = int(command['args'][0])
            frames_present = True
        elif c == 'vary':
            vary = True
        elif c == 'basename':
            basename = command['args'][0]
            basename_present = True
    if vary_present and not frames_present:
        print("vary present but not frames")
        exit(1)
    elif frames_present and not basename_present:
        basename = 'default'
        print("basename not found, set as default")
    return basename, num_frames
        

"""======== second_pass( commands ) ==========

  In order to set the knobs for animation, we need to keep
  a seaprate value for each knob for each frame. We can do
  this by using an array of dictionaries. Each array index
  will correspond to a frame (eg. knobs[0] would be the first
  frame, knobs[2] would be the 3rd frame and so on).

  Each index should contain a dictionary of knob values, each
  key will be a knob name, and each value will be the knob's
  value for that frame.

  Go through the command array, and when you find vary, go
  from knobs[0] to knobs[frames-1] and add (or modify) the
  dictionary corresponding to the given knob with the
  appropirate value.
  ===================="""
def second_pass( commands, num_frames ):
    frames = [{} for i in range(num_frames)]
    for command in commands:
        c = command['op']
        if c == 'vary':
            args = command['args']
            knob = command['knob']
            start_frame, end_frame = args[0:2]
            start_val, end_val = args[2:]
            if start_frame < 0 or end_frame >= num_frames or end_frame < start_frame:
                print("Invalid args for knob " + knob)
                exit(1)
            unit_change = 1.0 * (end_val - start_val)/(end_frame - start_frame)
            for frame in range(num_frames):
                if frame >= start_frame and frame <= end_frame:
                    frames[frame][knob] = start_val + unit_change * (frame - start_frame)
    return frames

def third_pass(symbols):
    lights = {}
    ambient = [50, 50, 50]
    for symbol in symbols:
        if symbols[symbol][0] == 'light':
            lights[symbol] = symbols[symbol][1]
        elif symbol == 'ambient':
            ambient = symbols[symbol][1:]
    return lights, ambient

def run(filename):
    """
    This function runs an mdl script
    """
    
    
    p = mdl.parseFile(filename)
    
    if p:
        (commands, symbols) = p
    else:
        print "Parsing failed."
        return
    
    basename, num_frames = first_pass(commands)
    frames = second_pass(commands, num_frames)
    lights, ambient = third_pass(symbols)
    
    for frame_num in range(num_frames):
        view = [0,
                0,
                1];
        ambient = [50,
                   50,
                   50]
        light = [[0.5,
                  0.75,
                  1],
                 [0,
                  255,
                  255]]
        areflect = [0.1,
                    0.1,
                    0.1]
        dreflect = [0.5,
                    0.5,
                    0.5]
        sreflect = [0.5,
                    0.5,
                    0.5]
        color = [0, 0, 0]
        knob_val = 1

        tmp = new_matrix()
        ident( tmp )

        stack = [ [x[:] for x in tmp] ]
        screen = new_screen()
        zbuffer = new_zbuffer()
        tmp = []
        step_3d = 20
        consts = ''
        coords = []
        coords1 = []
        knob_value = 1
        
        if num_frames > 1:
            for knob in frames[frame_num]:
                symbols[knob][1] = frames[frame_num][knob]
                
        for command in commands:
            c = command['op']
            args = command['args']
            
            if c in ['move', 'scale', 'rotate'] and command['knob']:
                knob_val = symbols[command['knob']][1]

            
            if c == 'box':
                if isinstance(args[0], str):
                    consts = args[0]
                    args = args[1:]
                if isinstance(args[-1], str):
                    coords = args[-1]
                add_box(tmp,
                        args[0], args[1], args[2],
                        args[3], args[4], args[5])
                matrix_mult( stack[-1], tmp )
                draw_polygons(tmp, screen, zbuffer, view, ambient, lights, symbols[command['constants']][1])
                tmp = []
            elif c == 'sphere':
                add_sphere(tmp,
                           args[0], args[1], args[2], args[3], step_3d)
                matrix_mult( stack[-1], tmp )
                draw_polygons(tmp, screen, zbuffer, view, ambient, lights, symbols[command['constants']][1])
                tmp = []
            elif c == 'torus':
                add_torus(tmp,
                          args[0], args[1], args[2], args[3], args[4], step_3d)
                matrix_mult( stack[-1], tmp )
                draw_polygons(tmp, screen, zbuffer, view, ambient, lights, symbols[command['constants']][1])
                tmp = []
            elif c == 'line':
                if isinstance(args[0], str):
                    consts = args[0]
                    args = args[1:]
                if isinstance(args[3], str):
                    coords = args[3]
                    args = args[:3] + args[4:]
                if isinstance(args[-1], str):
                    coords1 = args[-1]
                add_edge(tmp,
                         args[0], args[1], args[2], args[3], args[4], args[5])
                matrix_mult( stack[-1], tmp )
                draw_lines(tmp, screen, zbuffer, color)
                tmp = []
            elif c == 'move':
                tmp = make_translate(args[0] * knob_val, args[1] * knob_val, args[2] * knob_val)
                matrix_mult(stack[-1], tmp)
                stack[-1] = [x[:] for x in tmp]
                tmp = []
            elif c == 'scale':
                tmp = make_scale(args[0] * knob_val, args[1] * knob_val, args[2] * knob_val)
                matrix_mult(stack[-1], tmp)
                stack[-1] = [x[:] for x in tmp]
                tmp = []
            elif c == 'rotate':
                theta = args[1] * (math.pi/180) * knob_val
                if args[0] == 'x':
                    tmp = make_rotX(theta)
                elif args[0] == 'y':
                    tmp = make_rotY(theta)
                else:
                    tmp = make_rotZ(theta)
                matrix_mult( stack[-1], tmp )
                stack[-1] = [ x[:] for x in tmp]
                tmp = []
            elif c == 'push':
                stack.append([x[:] for x in stack[-1]] )
            elif c == 'pop':
                stack.pop()
            elif c == 'display':
                display(screen)
            elif c == 'save':
                save_extension(screen, args[0])
        if num_frames > 1:
            frame_name = 'anim/%s%03d.png' % (basename, frame_num)
            print 'Saving frame: ' + str(frame_num)
            save_extension( screen, frame_name )
    if num_frames > 1:
        make_animation(basename)
