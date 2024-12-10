import time
import keyboard # type: ignore
import pygame
import random
fontset = [
                0xF0, 0x90, 0x90, 0x90, 0xF0,		
                0x20, 0x60, 0x20, 0x20, 0x70,		
                0xF0, 0x10, 0xF0, 0x80, 0xF0,		
                0xF0, 0x10, 0xF0, 0x10, 0xF0,		
                0x90, 0x90, 0xF0, 0x10, 0x10,		
                0xF0, 0x80, 0xF0, 0x10, 0xF0,		
                0xF0, 0x80, 0xF0, 0x90, 0xF0,		
                0xF0, 0x10, 0x20, 0x40, 0x40,		
                0xF0, 0x90, 0xF0, 0x90, 0xF0,		
                0xF0, 0x90, 0xF0, 0x10, 0xF0,		
                0xF0, 0x90, 0xF0, 0x90, 0x90,		
                0xE0, 0x90, 0xE0, 0x90, 0xE0,		
                0xF0, 0x80, 0x80, 0x80, 0xF0,		
                0xE0, 0x90, 0x90, 0x90, 0xE0,		
                0xF0, 0x80, 0xF0, 0x80, 0xF0,		
                0xF0, 0x80, 0xF0, 0x80, 0x80		
        ]


class Chip8:
    def __init__(self):
        self.memory = [0] * 4096
        self.register = [0] * 16
        self.index_register = 0

        self.program_counter = 0x200
        self.stack_pointer = -1
        self.stack = [0]*16
        self.load_fontset()
        self.keypad = [0]*17

        #timers
        self.delay_timer = 0
        self.sound_timer = 0
        self.last_update = time.time()
 

        #pygame
        pygame.init()
        pygame.mixer.init()
        self.delay = 1
        self.screen_width = 64
        self.screen_height = 32
        self.screen = [[0] * self.screen_width for _ in range(self.screen_height)]
        self.scale = 10
        self.info_height = 60
        self.font = pygame.font.Font(None, 24)
        self.window = pygame.display.set_mode((self.screen_width * self.scale, self.screen_height * self.scale + self.info_height))
        pygame.display.set_caption("CHIPPY 8")

        #sound
        self.beep_sound = pygame.mixer.Sound("beep.wav")
        
        
    def load_fontset(self):
        self.memory[:0 + len(fontset)] = fontset


    def load_rom (self, rom_path):
        with open(rom_path, 'rb') as file:
            rom_data = file.read()
            self.memory[0x200:0x200 + len(rom_data)] = rom_data  
            #print(self.memory[0x200:0x200 + 0x4])

    def increase_program_counter(self):
        self.program_counter = self.program_counter + 2

    def read_instruction(self):
        # Combine two bytes to form a 16-bit instruction
        inst = (self.memory[self.program_counter] << 8) | self.memory[self.program_counter + 1]
        self.increase_program_counter()
        
        # Process the instruction
        self.process_instruction(inst)

    def process_instruction(self, instruction):
        # Mask and extract each part of the instruction in hexadecimal
        opcode = (instruction & 0xF000) >> 12  # Extract the first nibble (opcode)
        x = (instruction & 0x0F00) >> 8        # Extract the second nibble (register x)
        y = (instruction & 0x00F0) >> 4        # Extract the third nibble (register y)
        n = instruction & 0x000F               # Extract the fourth nibble (4-bit value)
        kk = instruction & 0x00FF              # Extract the last 8 bits (byte)
        nnn = instruction & 0x0FFF             # Extract the last 3 digits
        
        # Debug output: Print the instruction's components in hexadecimal
        print(f"Opcode: {hex(opcode)} X: {x} Y: {y} N: {n} KK: {hex(kk)}")
        print(hex(instruction))
        # Process instructions based on opcode (in hex format)
        if opcode == 0:  
            if kk == 0xee:
                self.program_counter = self.stack[self.stack_pointer]
                self.stack_pointer = self.stack_pointer - 1
                #print("Retun FRM SUBRTINE GOING TO TOP OF STACK: " + str(self.stack_pointer))
            else:
                self.clear_screen()
                #print("Clearing screen")
        if opcode == 0x1:
            self.program_counter = nnn
           # print("JUMP " + str(nnn))
        if opcode == 0x2:
            self.stack_pointer = self.stack_pointer + 1
            self.stack[self.stack_pointer] = self.program_counter
            self.program_counter = nnn
           # print("CALL ADDRESS AT" + str(nnn) + " STACK POINTER AT " + str(self.stack_pointer))
        if opcode == 0x3:
            if self.register[x] == kk:
                self.increase_program_counter()
                #print("Register " + str(x) + " == " + str(kk) + "SKIP NXT INSTR")
        if opcode == 0x4:
            if self.register[x] != kk:
                self.increase_program_counter()
                #print("Register " + str(x) + " != " + str(kk) + "SKIP NXT INSTR")
        if opcode == 0x5:
            if self.register[x] == self.register[y]:
                self.increase_program_counter()
                #print("REG " + str(x) + " == REG" + str(y) + "SKIP NXT INSTR")
        if opcode == 0x6:  # LD Vx, byte instruction
            self.register[x] = kk
           # print("SET REG " + str(x) + " byte inst " + str(kk))  
        if opcode == 0x7:
            self.register[x] = (self.register[x] + kk) & 0xFF
            #print("ADD KK " + str(kk) + " to Reg " + str(kk))

        if opcode == 0x8:
            if n == 0x0:
                self.register[x] = self.register[y]
               # print("REG Y Stored in X")
            elif n == 0x1:
                self.register[x] = self.register[x] | self.register[y]
               # print("BITWISE OR on REG " + str(x) + " & " + str(y))
            elif n == 0x2:
                self.register[x] = self.register[x] & self.register[y]
                #print("BITWISE AND& on REG " + str(x) + " & " + str(y))
            elif n == 0x3:
                self.register[x] = self.register[x] ^ self.register[y]
                #print("BITWISE XOR on REG " + str(x) + " & " + str(y))
            elif n == 0x4:
                og = self.register[x]
                result = (self.register[x] + self.register[y])  % 256

                self.register[x] = result

                #set carry flag if over 255
                if (og + self.register[y]) > 0xFF:
                    self.register[0xf] = 0x01
                else:
                    self.register[0xf] = 0x00
                
            elif n == 0x5:
                og = self.register[x]
                self.register[x] = (self.register[x] - self.register[y])  % 256
                if og >= self.register[y]:
                    self.register[0xf] = 0x01
                else:
                    self.register[0xf] = 0x00
                
                    
            elif n == 0x6:
                lms = self.register[x] & 0x01
                og = self.register[x]
                self.register[x] = og >> 1
                self.register[0xf] = lms


            elif n == 0x7:
                og = self.register[y]
                self.register[x] = (self.register[y] - self.register[x]) % 256
                if og > self.register[x]:
                    self.register[0xf] = 1
                else:
                    self.register[0xf] = 0
                
            elif n == 0xE:
                msb = (self.register[x] >> 7) & 0x01
                
                self.register[x] = (self.register[x] << 1) & 0xFF
                self.register[0xf] = msb
                
        if opcode == 0x9:
            if self.register[x] != self.register[y]:
                self.increase_program_counter()
                #print("REG:" + str(x) + " != " + "REG " + str(y) + " SKIPPING")
        if opcode == 0xa:  
           # print("Set I " + str(nnn))
            self.index_register = nnn  
        if opcode == 0xb:
            self.program_counter = nnn + self.register[0]
        if opcode == 0xc:
            random_byte = random.randint(0,255)
            self.register[x] = random_byte & kk
        if opcode == 0xd:
            self.draw_sprite(self.register[x], self.register[y], n)
           # print("DRAW")

        if opcode == 0xf:

            if kk == 0x1E:
                self.index_register = self.index_register + self.register[x]
            if kk == 0x07:
                self.register[x] = self.delay_timer
            if kk == 0x15:
                self.delay_timer = self.register[x]
            if kk == 0x18:
                self.sound_timer = self.register[x]
            if kk == 0x29:
                SPRITE_SIZE = 5
                digit = self.register[x]
                self.index_register = digit * SPRITE_SIZE

            if kk == 0x33:
                sep = int(self.register[x])
                h = sep // 100
                t = (sep % 100) // 10
                o = sep % 10
                self.memory[self.index_register] = h
                self.memory[self.index_register + 1] = t
                self.memory[self.index_register + 2] = o

            if kk == 0x55:
                for reg in range (x + 1):
                    self.memory[self.index_register + reg] = self.register[reg]
                    
           # print("SAVING")
            if kk == 0x65:
                for reg in range(x + 1):
                    self.register[reg] = self.memory[self.index_register + reg]
            #print("LOADING")
            #KEYBOARD
            if kk == 0x0A:  # Fx0A: Wait for a key press and store it in Vx
                key_pressed = False
                while not key_pressed:
                    self.handle_key_input()
                    for key, state in enumerate(self.keypad):
                        if state == 1:  # If key is pressed
                            self.register[x] = key  # Store the key in Vx
                            key_pressed = True
                            break
        #KEYBOARD
        if opcode == 0xe:
            if kk == 0x9E:
                if self.keypad[self.register[x]] == 1:
                    self.increase_program_counter()
            if kk == 0xA1:
                if self.keypad[self.register[x]] == 0:
                    self.increase_program_counter()


    def clear_screen(self):
        # Convert the screen array to Pygame-friendly format
        for y in range(self.screen_height):
            for x in range(self.screen_width):
                self.screen[y][x] = 0
                self.draw_screen()

    def draw_info(self):
        # Fill the extra space for info with black
        pygame.draw.rect(
            self.window,
            (0, 0, 0),
            (0, self.screen_height * self.scale, self.screen_width * self.scale, self.info_height)
        )
        
        # Display program counter and current instruction
        current_instruction = (self.memory[self.program_counter] << 8) | self.memory[self.program_counter + 1]
        pc_text = "Program Counter: " + hex(self.program_counter) + "  " + str(self.program_counter)
        inst_text = "Current Instruction: " + hex(current_instruction)
        
        # Render the text for program counter
        pc_surface = self.font.render(pc_text, True, (255, 255, 255))
        self.window.blit(pc_surface, (10, self.screen_height * self.scale + 10))
        
        # Render the text for current instruction
        inst_surface = self.font.render(inst_text, True, (255, 255, 255))
        self.window.blit(inst_surface, (10, self.screen_height * self.scale + 40))

    def draw_screen(self):
        # Convert the screen array to Pygame-friendly format
        for y in range(self.screen_height):
            for x in range(self.screen_width):
                color = (255, 255, 255) if self.screen[y][x] else (0, 0, 0)
                pygame.draw.rect(
                    self.window,
                    color,
                    (x * self.scale, y * self.scale, self.scale, self.scale)
                )
        pygame.display.flip()

    def draw_sprite(self, x, y, n_bytes):
        collision = 0  # Track if any pixel was turned off & set the VF register 0xf if there is an overlap
        for byte_index in range(n_bytes):
            sprite_byte = self.memory[self.index_register + byte_index]
            for bit_index in range(8):
                # Get the current pixel value (0 or 1)
                pixel = (sprite_byte >> (7 - bit_index)) & 1
                if pixel:  # Only draw if the sprite pixel is ON
                    screen_x = (x + bit_index) % self.screen_width  # Wrap horizontally
                    screen_y = (y + byte_index) % self.screen_height  # Wrap vertically

                    # XOR operation on the screen pixel
                    current_pixel = self.screen[screen_y][screen_x]
                    self.screen[screen_y][screen_x] ^= pixel

                    # Check for collision
                    if current_pixel and not self.screen[screen_y][screen_x]:
                        collision = 1
        if collision:
            self.register[0xf] = 1
    def update_timers(self):
        current_time = time.time()
        elapsed_time = current_time - self.last_update

        if elapsed_time >= 1/60:
            decrement_steps = int(elapsed_time // (1/60))  # How many 60Hz steps passed
            self.last_update += decrement_steps * (1/60)  # Update last timer time

            # Decrease the timers, ensuring they don't go below 0
            if self.delay_timer > 0:
                self.delay_timer = max(0, self.delay_timer - decrement_steps)
            if self.sound_timer > 0:
                self.sound_timer = max(0, self.sound_timer - decrement_steps)

        if self.sound_timer > 0:
            if not pygame.mixer.get_busy():
                self.beep_sound.play()
        else:
            self.beep_sound.stop()

    def handle_key_input(self):
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.keypad[1] = 1
                    elif event.key == pygame.K_2:
                        self.keypad[2] = 1
                    elif event.key == pygame.K_3:
                        self.keypad[3] = 1
                    elif event.key == pygame.K_4:
                        self.keypad[0x0C] = 1
                    elif event.key == pygame.K_q:
                        self.keypad[4] = 1
                    elif event.key == pygame.K_w:
                        self.keypad[5] = 1
                    elif event.key == pygame.K_e:
                        self.keypad[6] = 1
                    elif event.key == pygame.K_r:
                        self.keypad[0x0D] = 1
                    elif event.key == pygame.K_a:
                        self.keypad[7] = 1
                    elif event.key == pygame.K_s:
                        self.keypad[8] = 1
                    elif event.key == pygame.K_d:
                        self.keypad[9] = 1
                    elif event.key == pygame.K_f:
                        self.keypad[0x0E] = 1
                    elif event.key == pygame.K_z:
                        self.keypad[0x0A] = 1
                    elif event.key == pygame.K_x:
                        self.keypad[0] = 1
                    elif event.key == pygame.K_c:
                        self.keypad[0x0B] = 1
                    elif event.key == pygame.K_v:
                        self.keypad[0x0F] = 1
                    elif event.key == pygame.K_ESCAPE:
                        quit()
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_1:
                        self.keypad[1] = 0
                    elif event.key == pygame.K_2:
                        self.keypad[2] = 0
                    elif event.key == pygame.K_3:
                        self.keypad[3] = 0
                    elif event.key == pygame.K_4:
                        self.keypad[0x0C] = 0
                    elif event.key == pygame.K_q:
                        self.keypad[4] = 0
                    elif event.key == pygame.K_w:
                        self.keypad[5] = 0
                    elif event.key == pygame.K_e:
                        self.keypad[6] = 0
                    elif event.key == pygame.K_r:
                        self.keypad[0x0D] = 0
                    elif event.key == pygame.K_a:
                        self.keypad[7] = 0
                    elif event.key == pygame.K_s:
                        self.keypad[8] = 0
                    elif event.key == pygame.K_d:
                        self.keypad[9] = 0
                    elif event.key == pygame.K_f:
                        self.keypad[0x0E] = 0
                    elif event.key == pygame.K_z:
                        self.keypad[0X0A] = 0
                    elif event.key == pygame.K_x:
                        self.keypad[0] = 0
                    elif event.key == pygame.K_c:
                        self.keypad[0x0B] = 0
                    elif event.key == pygame.K_v:
                        self.keypad[0x0F] = 0


cpu = Chip8()
cpu.load_rom('5-quirks.ch8')
cpu.sound_timer = 21
while True:

    cpu.handle_key_input()
    cpu.read_instruction()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit()


    pygame.time.delay(cpu.delay)
    cpu.draw_screen()
    cpu.draw_info() 
    cpu.update_timers()



