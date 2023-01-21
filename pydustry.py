import pygame, os, sys, csv, json, math, pygame_menu
from pygame.locals import *
pygame.init()

"""--------*Variables-initialization*----------"""

# ---------------------------------------------- #

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 760
enemyDelay = 0
frames = turretFrames = 0
enemyFrames = 0
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
allBuildings = pygame.sprite.Group()
tileMap = pygame.sprite.Group()
bullets = pygame.sprite.Group()
enemy = pygame.sprite.Group()
WIDTH: int = 1000
HEIGHT: int = 700
RESOLUTION: int = 32

# ---------------------------------------------- #

"""----------*Some-useful-functions*-----------"""


# ---------------------------------------------- #

def extend(obj: any, key: int) -> None:
    obj.rect.x, obj.rect.y = obj.rect.x + ((-1) * key), obj.rect.y + ((-1) * key)
    obj.rect.width, obj.rect.height = obj.rect.width + (2 * key), obj.rect.height + (2 * key)

# ---------------------------------------------- #

def dictl(it: list[tuple[str, int]]) -> dict[str: int]:
    result: dict = dict()
    for i in it:
        result[i[0]] = i[1]
    return result

# ---------------------------------------------- #

def loadImage(name: str, colorkey: int = None) -> pygame.Surface:
    try:
        image = pygame.image.load(os.path.join('data', name)).convert()
    except FileNotFoundError:
        print('Cannot load image:', name)
        return loadImage('NoTexture.png')

    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


# ---------------------------------------------- #

def terminate():
    pygame.quit()
    sys.exit()

# ---------------------------------------------- #

"""----------------*Resources*-----------------"""

# ---------------------------------------------- #

class Resource:
    name: str

    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return self.name

# ---------------------------------------------- #

class RequiredResource:
    resource: Resource
    count: int

    def __init__(self, resource: Resource, count: int) -> None:
        self.resource, self.count = resource, count

# ---------------------------------------------- #

"""-------------*Static-objects*---------------"""

# ---------------------------------------------- #

class Building(pygame.sprite.Sprite):
    size: int
    center: tuple[int, int]
    image: pygame.Surface
    rect: pygame.Rect
    durability: int

    def __init__(self, size: int, center: tuple[int, int], durability: int, imageName: str, required={'copper': 1}):
        super().__init__()
        self.size, self.center, self.durability, self.image = size - 1, center, durability, loadImage(imageName)
        self.health = durability
        self.rect = self.image.get_rect()
        self.rect.x = center[0] * RESOLUTION - (size - 1) * RESOLUTION
        self.rect.y = center[1] * RESOLUTION - (size - 1) * RESOLUTION
        self.req = required

    def draw(self, surface):
        self.rect.x = self.center[0] * RESOLUTION - (self.size - 1) * RESOLUTION
        self.rect.y = self.center[1] * RESOLUTION - (self.size - 1) * RESOLUTION
        surface.blit(self.image, (self.rect.x, self.rect.y))
    
    def update(self, *args, **kwargs) -> None:
        if self.durability <= 0:
            self.kill()
            del self

# ---------------------------------------------- #

class Factory(Building):
    resources: list[RequiredResource]
    production: Resource
    inventory: list[Resource]

    def __init__(self, size: int, center: tuple[int, int], durability: int, imageName: str,
                 resources: list[tuple[Resource, int]], production: Resource, req={'copper': 1}) -> None:
        super().__init__(size, center, durability, imageName, required=req)
        self.resources = list(map(lambda x: RequiredResource(*x), resources))
        self.production, self.inventory = production, []

    def get_resource(self, resource: Resource) -> None:
        init = list(map(lambda x: x.resource.name, self.resources))
        if resource.name in init:
            self.inventory.append(resource)

    def produce(self) -> Resource:
        flag: bool = True
        inv = list(map(lambda x: x.name, self.inventory))
        it = list(set(inv))
        res = dictl(list(map(lambda x: (x.resource.name, x.count), self.resources)))
        for i in it:
            if inv.count(i) < res[i]:
                flag = False
        if flag and it:
            self.inventory.clear()
        return self.production if flag and it else None

    def update(self, *args, **kwargs):
        super().update(self)
        extend(self, 1)
        self.output(self.produce())
        extend(self, -1)

    def output(self, resource: Resource):
        for building in pygame.sprite.spritecollide(self, allBuildings, False):
            if (type(building) is Conveyor or type(building) is Factory) and self != building:
                if type(building) is Conveyor:
                    if not building.dot(self):
                        building.get_resource(resource)
                else:
                    building.get_resource(resource)

# ---------------------------------------------- #

class Conveyor(Building):
    direction: tuple[int, int]
    init: Resource | None

    def __init__(self, size: int, center: tuple[int, int], durability: int, imageName: str, direction: tuple[int, int],
    req={'copper': 1}):
        super().__init__(size, center, durability, imageName, required=req)
        self.direction, self.init = direction, None
        self.updated = False

    def get_resource(self, resource: Resource):
        global player
        if self.init is None:
            self.init = resource
            self.updated = True
            if self.init is not None:
                self.image.blit(loadImage(f"{self.init.name}.png", colorkey=(0, 0, 0)), (0, 0))
                print(player.inventory)

    def update(self):
        super().update(self)
        if not self.updated:
            global frames, player, Map
            if frames % 100 == 0:
                if self.init is not None:
                    self.image.blit(loadImage(f"{self.init.name}.png", colorkey=(0, 0, 0)), (0, 0))
                else:
                    self.image = loadImage("rail.png")
                    dec = {(0, -1): 0, (1, 0): 270, (0, 1): 180, (-1, 0): 90}
                    self.image = pygame.transform.rotate(self.image, dec[self.direction])
                if self.init is not None:
                    dot = [self.rect.x + RESOLUTION // 2, self.rect.y + RESOLUTION // 2]
                    dot[0] += self.direction[0] * RESOLUTION
                    dot[1] += self.direction[1] * RESOLUTION
                    extend(self, 1)
                    for building in pygame.sprite.spritecollide(self, allBuildings, False):
                        if (type(building) is Conveyor or type(building) is Factory) and building != self:
                            if building.rect.collidepoint(dot):
                                if type(building) is Conveyor:
                                    if building.init is None:
                                        building.get_resource(self.init)
                                        self.init = None
                                else:
                                    building.get_resource(self.init)
                                    self.init = None
                    for tile in pygame.sprite.spritecollide(self, Map.tiles, False):
                        if type(tile) is Core:
                            if tile.rect.collidepoint(dot):
                                tile.get_resource(self.init, player)
                                self.init = None
                    if self.init is None:
                        self.image = loadImage("rail.png")
                        dec = {(0, -1): 0, (1, 0): 270, (0, 1): 180, (-1, 0): 90}
                        self.image = pygame.transform.rotate(self.image, dec[self.direction])
                    del dot
                    extend(self, -1)
                frames = 0
        self.updated = False
    
    def draw(self, surface):
        dec = {(0, -1): 0, (1, 0): 90, (0, 1): 180, (-1, 0): 270}
        self.image = pygame.transform.rotate(self.image, dec[self.direction])
        surface.blit(self.image)
    
    def dot(self, obj):
        dot = [self.rect.x + RESOLUTION // 2, self.rect.y + RESOLUTION // 2]
        dot[0] += self.direction[0] * RESOLUTION
        dot[1] += self.direction[1] * RESOLUTION
        if obj.rect.collidepoint(dot):
            return True
        return False

# ---------------------------------------------- #

class Drill(Building):
    speed: int

    def __init__(self, size: int, center: tuple[int, int], speed: int, durability: int, imageName: str,
    req={'copper': 1}):
        super().__init__(size, center, durability, imageName, required=req)
        self.speed = speed

    def update(self):
        global Map
        super().update(self)
        extend(self, 1)
        for tile in pygame.sprite.spritecollide(self, Map.tiles, False):
            if type(tile) is Ore:
                self.output(tile.gives)
        extend(self, -1)

    def output(self, resource: Resource):
        for building in pygame.sprite.spritecollide(self, allBuildings, False):
            if type(building) is Conveyor or type(building) is Factory:
                if type(building) is Conveyor:
                    if not building.dot(self):
                        building.get_resource(resource)
                else:
                    building.get_resource(resource)

# ---------------------------------------------- #

class Turret(Building):
    def update(self) -> None:
        global enemy, turretFrames
        if turretFrames % 1000 == 0:
            for i in enemy:
                GoodBullet(3, i, (self.rect.x, self.rect.y))
                break
            turretFrames = 0

# ---------------------------------------------- #

class Wall(Building): pass

# ---------------------------------------------- #

"""----------------*Entities*------------------"""

# ---------------------------------------------- #

class Bullet(pygame.sprite.Sprite):
    def __init__(self, damage, target: pygame.sprite.Sprite, pos) -> None:
        super().__init__(bullets)
        self.damage, self.target = damage, target
        self.image = loadImage('bullet.png', colorkey=(0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = pos
    
    def draw(self, surface):
        surface.blit(self.image, (self.rect.x, self.rect.y))

class EnemyBullet(Bullet):
    def update(self) -> None:
        global allBuildings, Map
        act = False
        try:
            self.rect.x += 1 if self.target.rect.x > self.rect.x else -1
            self.rect.y += 1 if self.target.rect.y > self.rect.y else -1
            for i in pygame.sprite.spritecollide(self, allBuildings, False):
                i.durability -= 10
                act = True
            for i in pygame.sprite.spritecollide(self, Map.tiles, False):
                if type(i) is Core:
                    i.durability -= self.damage
                    print(i.durability)
                    act = True
            if act:
                self.kill()
                del self
        except Exception:
            self.kill()
            del self

class GoodBullet(Bullet):
    def update(self) -> None:
        global enemy
        act = False
        try:
            self.rect.x += 1 if self.target.rect.x > self.rect.x else -1
            self.rect.y += 1 if self.target.rect.y > self.rect.y else -1
            for i in pygame.sprite.spritecollide(self, enemy, False):
                i.health -= self.damage
                act = True
                break
            if act:
                self.kill()
                del self
        except Exception:
            self.kill()
            del self

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = loadImage("Player.png", colorkey=(0, 0, 0))
        self.rect = self.image.get_rect()
        self.image0 = self.image.copy()
        self.image90 = pygame.transform.rotate(self.image, 90)
        self.image180 = pygame.transform.rotate(self.image, 180)
        self.image270 = pygame.transform.rotate(self.image, 270)
        self.rect.center = (160, 520)
        self.inventory = {'copper': 50,
                          'lead': 0,
                          'silicon': 0,}

    def update(self):
        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[K_a]:
            self.rect.move_ip(-1, 0)
            self.image = self.image90.copy()
        if pressed_keys[K_d]:
            self.rect.move_ip(1, 0)
            self.image = self.image270.copy()
        if pressed_keys[K_w]:
            self.rect.move_ip(0, -1)
            self.image = self.image0.copy()
        if pressed_keys[K_s]:
            self.rect.move_ip(0, 1)
            self.image = self.image180.copy()

    def draw(self, surface):
        surface.blit(self.image, self.rect)
    
    def add(self, resource: Resource):
        if resource is not None:
            if resource.name in self.inventory.keys():
                self.inventory[resource.name] += 1
            else:
                self.inventory[resource.name] = 1
        print(self.inventory)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, health, core) -> None:
        global Map
        super().__init__(enemy)
        self.health = health
        self.image = loadImage('enemy.png', colorkey=(0, 0, 0))
        self.rect = self.image.get_rect()
        self.core = core
        for tile in Map.tiles:
            if type(tile) is Spawn:
                self.rect.x, self.rect.y = tile.rect.x, tile.rect.y
    
    def draw(self, surface):
        surface.blit(self.image, (self.rect.x, self.rect.y))

    def update(self):
        global enemyFrames, allBuildings, Map
        if enemyFrames % 1000 == 0:
            if allBuildings:
                for i in allBuildings:
                    EnemyBullet(7, i, (self.rect.x, self.rect.y))
                    break
            else:
                for tile in Map.tiles:
                    if type(tile) is Core:
                        EnemyBullet(7, tile, (self.rect.x, self.rect.y))
            enemyFrames = 0
        else:
            self.rect.x += 1 if self.core.rect.x > self.rect.x else -1
            self.rect.y += 1 if self.core.rect.x > self.rect.x else -1
        if self.health <= 0:
            self.kill()

# ---------------------------------------------- #

class Camera:
    def __init__(self):
        self.dx = 0
        self.dy = 0

    def apply(self, obj):
        obj.rect.x += self.dx
        obj.rect.y += self.dy

    def update(self, target):
        self.dx = -(target.rect.x + target.rect.w // 2 - SCREEN_WIDTH // 2)
        self.dy = -(target.rect.y + target.rect.h // 2 - SCREEN_HEIGHT // 2)

# ---------------------------------------------- #

"""---------------*Map-parts*------------------"""

"""--------------------------------------------"""

class Shadow(pygame.sprite.Sprite):
    def __init__(self, building: any) -> None:
        super().__init__()
        self.building = building

    def build(self, group: pygame.sprite.Group(), cursor: tuple[int, int], tiles: pygame.sprite.Group()) -> None:
        x, y = cursor
        global player
        for i in self.building.req.keys():
            if player.inventory[i] < self.building.req[i]:
                return None
            for i in group:
                if i.rect.collidepoint(x, y):
                    return None
            else:
                flag = False
                for i in tiles:
                    i.rect.width = i.rect.height = RESOLUTION
                    if i.rect.collidepoint(x, y) and type(i) is not Void:
                        flag = True
                        x, y = i.rect.x, i.rect.y
                if flag:
                    self.building.rect.x, self.building.rect.y = x, y
                    if type(self.building) is Conveyor:
                        dec = {(0, 1): 180, (-1, 0): 90, (0, -1): 0, (1, 0): 270}
                        self.building.image = pygame.transform.rotate(self.building.image, dec[self.building.direction])
                    group.add(self.building)
                    for i in self.building.req.keys():
                        player.inventory[i] -= self.building.req[i]

    def draw(self, surface, cursor: tuple[int, int], tiles: pygame.sprite.Group()) -> None:
        x, y = cursor
        for i in tiles:
            i.rect.width = i.rect.height = RESOLUTION
            if i.rect.collidepoint(x, y):
                x, y = i.rect.x, i.rect.y
        if type(self.building) is Conveyor:
            dec = {(0, 1): 180, (-1, 0): 90, (0, -1): 0, (1, 0): 270}
            surface.blit(pygame.transform.rotate(self.building.image, dec[self.building.direction]), (x, y))
        else:
            surface.blit(self.building.image, (x, y))

"""------------------*Map*---------------------"""

# ---------------------------------------------- #

class Spritesheet:
    def __init__(self, filename):
        self.filename = filename
        self.sprite_sheet = pygame.image.load(f"{filename}").convert()
        self.meta_data = self.filename.replace('png', 'json')
        with open(self.meta_data) as f:
            self.data = json.load(f)
        f.close()

    def get_sprite(self, x, y, w, h):
        sprite = pygame.Surface((w, h))
        sprite.blit(self.sprite_sheet, (0, 0), (x, y, w, h))
        return sprite

    def parse_sprite(self, name):
        sprite = self.data['frames'][name]['frame']
        x, y, w, h = sprite["x"], sprite["y"], sprite["w"], sprite["h"]
        image = self.get_sprite(x, y, w, h)
        return image

# ---------------------------------------------- #

class Tile(pygame.sprite.Sprite):
    def __init__(self, image, x, y, spritesheet):
        pygame.sprite.Sprite.__init__(self)
        self.image = spritesheet.parse_sprite(image)
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y

    def draw(self, surface):
        surface.blit(self.image, (self.rect.x, self.rect.y))

class Void(Tile): ...

class Spawn(Tile): ...

class Ore(Tile):
    def __init__(self, image, x, y, spritesheet, gives):
        super().__init__(image, x, y, spritesheet)
        self.gives = gives

class Core(Tile):
    durability = 100

    def get_resource(self, resource, inv):
        inv.add(resource)
    
    def update(self):
        if self.durability <= 0:
            self.kill()
            terminate()

# ---------------------------------------------- #

decoder: dict[str: str] = {'1': 'fl_sand.png', '2': 'lead_ore.png', '3': 'sand.png', '4': 'coal_ore.png',
                 '5': 'copper_ore.png', '6': 'spawn.png', '7': 'core.png', '9': 'background.png'}
coal = Resource('coal')
sand = Resource('sand')
copper = Resource('copper')
lead = Resource('lead')
silicon = Resource('silicon')
ores: dict[str: Resource] = {'coal_ore.png': coal, 'sand.png': sand, 'copper_ore.png': copper, 'lead_ore.png': lead}

class TileMap:
    def __init__(self, filename, spritesheet):
        self.tile_size = 32
        self.spritesheet = spritesheet
        self.tiles = self.load_tiles(filename)

    def draw_map(self, surface):
        for tile in self.tiles:
            tile.draw(surface)

    def read_csv(self, filename):
        __map = []
        with open(os.path.join(filename)) as data:
            data = csv.reader(data, delimiter=',')
            for row in data:
                __map.append(list(row))
        return __map

    def load_tiles(self, filename):
        tiles = pygame.sprite.Group()
        __map = self.read_csv(filename)
        x, y = 0, 0
        for row in __map:
            x = 0
            for tile in row:
                if tile in ['1', '6', '7', '9']:
                    if decoder[tile] == 'core.png':
                        tiles.add(Core(decoder[tile], x * self.tile_size, y * self.tile_size, self.spritesheet))
                    elif decoder[tile] == 'background.png':
                        tiles.add(Void(decoder[tile], x * self.tile_size, y * self.tile_size, self.spritesheet))
                    elif decoder[tile] == 'spawn.png':
                        tiles.add(Spawn(decoder[tile], x * self.tile_size, y * self.tile_size, self.spritesheet))
                    else:
                        tiles.add(Tile(decoder[tile], x * self.tile_size, y * self.tile_size, self.spritesheet))
                else:
                    global coal_ore, copper_ore, lead_ore, sand
                    t = Ore(decoder[tile], x * self.tile_size, y * self.tile_size, self.spritesheet, ores[decoder[tile]])
                    tiles.add(t)
                x += 1
            y += 1
        self.map_w = x * self.tile_size
        self.map_h = y * self.tile_size
        return tiles

# ---------------------------------------------- #

if __name__ == '__main__':
    spritesheet = Spritesheet('spritesheet.png')
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('PYDUSTRY')
    font = pygame_menu.font.FONT_8BIT
    myimage = pygame_menu.baseimage.BaseImage(image_path=pygame_menu.baseimage.IMAGE_EXAMPLE_GRAY_LINES,
                                            drawing_mode=pygame_menu.baseimage.IMAGE_MODE_REPEAT_XY,)
    mytheme = pygame_menu.Theme(background_color=myimage, widget_font=font, title_background_color=(4, 47, 126),
                                title_bar_style=pygame_menu.widgets.MENUBAR_STYLE_TITLE_ONLY_DIAGONAL)
    menu = pygame_menu.Menu('PYDUSTRY', 1200, 760, theme=mytheme)
    player = Player()
    running = True
    Map = None

    def start_the_game():
        global frames, player, running, enemyFrames, Map, enemyDelay
        Map = TileMap(selected, spritesheet)
        for tile in Map.tiles:
            if type(tile) is Core:
                player.rect.x, player.rect.y = tile.rect.x, tile.rect.y
                tile.rect.width = tile.rect.height = RESOLUTION
        camera = Camera()
        now_building = False
        screen.set_colorkey((0, 0, 0))
        tileMap = Map.tiles
        ok = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    terminate()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if now_building:
                            shadow.build(allBuildings, pygame.mouse.get_pos(), Map.tiles)
                            now_building = False
                    if event.button == 3:
                        if now_building:
                            del shadow
                            now_building = False
                        else:
                            x, y = event.pos
                            for i in Map.tiles:
                                i.rect.width = i.rect.height = RESOLUTION
                                if i.rect.collidepoint(x, y):
                                    x, y = i.rect.x, i.rect.y
                            for i in allBuildings:
                                if i.rect.collidepoint(x, y):
                                    i.kill()
                                    del i
                    if event.button == 2:
                        x, y = event.pos
                        for i in Map.tiles:
                            i.rect.width = i.rect.height = RESOLUTION
                            if i.rect.collidepoint(x, y):
                                x, y = i.rect.x, i.rect.y
                        for i in allBuildings:
                            if i.rect.collidepoint(x, y):
                                try:
                                    print(i.init)
                                    print(pygame.sprite.spritecollide(i, allBuildings, False))
                                except Exception:
                                    print(pygame.sprite.spritecollide(i, tileMap, False))
                                print(type(i))
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        shadow = Shadow(Conveyor(1, (0, 0), 1, 'rail.png', (0, -1)))
                        now_building = True
                    if event.key == pygame.K_DOWN:
                        shadow = Shadow(Conveyor(1, (0, 0), 1, 'rail.png', (0, 1)))
                        now_building = True
                    if event.key == pygame.K_RIGHT:
                        shadow = Shadow(Conveyor(1, (0, 0), 1, 'rail.png', (1, 0)))
                        now_building = True
                    if event.key == pygame.K_LEFT:
                        shadow = Shadow(Conveyor(1, (0, 0), 1, 'rail.png', (-1, 0)))
                        now_building = True
                    if event.key == pygame.K_1:
                        shadow = Shadow(Drill(1, (0, 0), 1, 20, 'drill.png', req={'copper': 10}))
                        now_building = True
                    if event.key == pygame.K_2:
                        shadow = Shadow(Factory(1, (0, 0), 40, 'silicon_oven.png', [(sand, 2), (coal, 2)], silicon,
                        req={'copper': 20, 'lead': 20}))
                        now_building = True
                    if event.key == pygame.K_3:
                        shadow = Shadow(Turret(1, (0, 0), 30, 'turret.png',
                        required={'lead': 20, 'silicon': 10}))
                        now_building = True
                    if event.key == pygame.K_4:
                        shadow = Shadow(Wall(1, (0, 0), 70, 'wall.png', required={'copper': 30}))
                        now_building = True
                    if event.key == pygame.K_x:
                        for i in enemy:
                            GoodBullet(10, i, (player.rect.x, player.rect.y))
                            break
                    if event.key == pygame.K_b:
                        for tile in Map.tiles:
                            if type(tile) is Core:
                                Enemy(10, tile)
            screen.fill((0, 0, 0))
            allBuildings.update()
            bullets.update()
            enemy.update()
            player.update()
            camera.update(player)
            camera.apply(player)
            for tile in allBuildings:
                camera.apply(tile)
            for tile in bullets:
                camera.apply(tile)
            for tile in Map.tiles:
                if type(tile) is Core:
                    tile.update()   
                camera.apply(tile)
            for tile in enemy:
                camera.apply(tile)
            Map.draw_map(screen)
            allBuildings.draw(screen)
            enemy.draw(screen)
            bullets.draw(screen)
            if now_building:
                pygame.mouse.get_pos()
                shadow.draw(screen, pygame.mouse.get_pos(), Map.tiles)
            player.draw(screen)
            pygame.display.flip()
            frames += 1
            enemyFrames += 1
            enemyDelay += 1
            for tile in Map.tiles:
                if type(tile) is Core:
                    tile.update()
            for tile in Map.tiles:
                if type(tile) is Core:
                    if enemyDelay % 10000 == 0:
                        Enemy(10, tile)
                        Enemy(10, tile)
                        enemyDelay = 0
            pygame.time.delay(1)
    
    selected = 'map_1.csv'
    menu.add.button('Play', start_the_game, font_size=150)
    menu.add.button('Exit', pygame_menu.events.EXIT, font_size=150)
    def set_map(value, map_):
        global selected
        if map_ == 2:
            selected = 'map_2.csv'
        elif map_ == 1:
            selected = 'map_1.csv'
    menu.add.selector('Maps :', [('Map1', 1), ('Map2', 2)], onchange=set_map)
    menu.mainloop(screen)
