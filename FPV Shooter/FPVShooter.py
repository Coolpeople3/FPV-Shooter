from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random
import os

# Custom method to load textures safely
def load_texture_safe(path):
    # Check if the texture exists
    if os.path.exists(path):
        return Texture(path)
    else:
        print(f"Warning: Texture {path} not found!")
        return None

# Initialize the game
app = Ursina()

# Game Variables
ammo_count = 10
player_health = 100
player_score = 0
enemies = []
bullets = []
healing_boxes = []
enemies_alive = 5
current_wave = 1
max_waves = 3
damage_cooldown = 0.5
healing_amount = 20
bullet_speed = 15  # Adjust bullet speed

# Setup the game world
ground = Entity(
    model='plane',
    scale=(100, 1, 100),
    texture=load_texture_safe('textures/grass.png'),
    texture_scale=(50, 50),
    collider='box'
)

# Sky setup with error handling
sky_texture = load_texture_safe('textures/sky_sunset.png')
if sky_texture:
    Sky(texture=sky_texture)

# Add walls and houses for cover
walls = []
houses = []

for _ in range(5):
    x = random.randint(-30, 30)
    z = random.randint(-30, 30)
    wall = Entity(
        model='cube',
        color=color.brown,
        position=(x, 1, z),
        scale=(5, 3, 1),
        texture=load_texture_safe('textures/brick.png'),
        collider='box'
    )
    walls.append(wall)

for _ in range(3):
    x = random.randint(-40, 40)
    z = random.randint(-40, 40)
    house = Entity(
        model='models/house.obj',
        texture=load_texture_safe('textures/house_texture.png'),
        position=(x, 1, z),
        scale=(8, 5, 8),
        collider='box'
    )
    houses.append(house)

# Player setup
player = FirstPersonController()

# UI Elements
ammo_display = Text(f"Ammo: {ammo_count}", position=(-0.85, 0.45), scale=2, background=True)
health_display = Text(f"Health: {player_health}", position=(-0.85, 0.4), scale=2, background=True)
score_display = Text(f"Score: {player_score}", position=(-0.85, 0.35), scale=2, background=True)
wave_display = Text(f"Wave: {current_wave}/{max_waves}", position=(-0.85, 0.3), scale=2, background=True)

# Enemy setup to keep the original lying down pose
def spawn_enemies(wave):
    global enemies, enemies_alive
    enemies_alive = wave * 5

    for _ in range(enemies_alive):
        x = random.randint(-40, 40)
        z = random.randint(-40, 40)

        # Zombie entity creation
        enemy = Entity(
            model='models/Zombie.obj',
            texture=load_texture_safe('textures/zombie.png'),
            position=(x, 0.5, z),  # Raise the zombie slightly off the ground
            collider='box',
            scale=0.05,
            color=color.rgb(210, 180, 140)  # Dark tan color for the zombie
        )

        # Reset zombie rotation to its original "lying down" pose (no rotation changes)
        enemy.rotation_x = 0  # Reset X rotation
        enemy.rotation_y = random.uniform(0, 360)  # Random Y rotation for varied facing
        enemy.rotation_z = 0  # Reset Z rotation to ensure no tilt

        enemies.append(enemy)

# Spawning initial enemies
spawn_enemies(current_wave)

# Healing box setup
def spawn_healing_box():
    x = random.randint(-40, 40)
    z = random.randint(-40, 40)
    healing_box = Entity(
        model='cube',
        color=color.green,
        position=(x, 1, z),
        collider='box',
        scale=(1, 1, 1)
    )
    healing_boxes.append(healing_box)

for _ in range(5):
    spawn_healing_box()

# Shooting mechanics
def shoot():
    global ammo_count
    if ammo_count > 0:
        # Cast a ray from the camera based on where the crosshair is pointing
        ray_origin = player.position + Vec3(0, 1.5, 0)  # Start just in front of the player
        ray_direction = player.forward  # Direction the camera is facing

        # Create the bullet and shoot it
        bullet = Entity(
            model='sphere',
            color=color.red,
            scale=(0.2, 0.2, 0.2),
            position=ray_origin,
            rotation=player.rotation,
            collider='box',
        )
        bullet.velocity = ray_direction * bullet_speed  # Move the bullet in the calculated direction
        bullets.append(bullet)
        ammo_count -= 1
        ammo_display.text = f"Ammo: {ammo_count}"

# Reload mechanics
def reload():
    global ammo_count
    ammo_count = 10
    ammo_display.text = f"Ammo: {ammo_count}"

# Update enemy behavior
def update_enemies():
    global player_health, enemies

    for enemy in enemies:
        if enemy.enabled:
            direction_to_player = (player.position - enemy.position).normalized()
            enemy.look_at(player.position)  # Enemy faces player
            if distance(enemy, player) > 1.5:
                enemy.position += direction_to_player * time.dt * 2
            elif distance(enemy, player) < 1.5:
                player_health -= 1
                health_display.text = f"Health: {player_health}"
                if player_health <= 0:
                    Text("Game Over!", scale=3, origin=(0, 0), background=True)
                    application.pause()

# Update game state
def update():
    global player_health, bullets, enemies_alive, current_wave, player_score

    update_enemies()  # Update enemy behavior

    for bullet in bullets:
        # Move the bullet in the direction of its velocity
        bullet.position += bullet.velocity * time.dt

        # Destroy bullet if it moves too far from the origin
        if bullet.position.length() > 100:
            destroy(bullet)
            bullets.remove(bullet)
            continue

        # Bullet-enemy collision
        if bullet.intersects().hit:
            hit_entity = bullet.intersects().entity
            if hit_entity in enemies:
                enemies.remove(hit_entity)
                destroy(hit_entity)
                enemies_alive -= 1
                player_score += 10
                score_display.text = f"Score: {player_score}"
                if enemies_alive == 0 and current_wave < max_waves:
                    current_wave += 1
                    wave_display.text = f"Wave: {current_wave}/{max_waves}"
                    spawn_enemies(current_wave)
                elif enemies_alive == 0 and current_wave == max_waves:
                    Text("You Win!", scale=3, origin=(0, 0), background=True)
                    application.pause()
            destroy(bullet)
            bullets.remove(bullet)

    for healing_box in healing_boxes:
        if distance(healing_box, player) < 1.5:
            player_health += healing_amount
            player_health = min(player_health, 100)
            health_display.text = f"Health: {player_health}"
            healing_boxes.remove(healing_box)
            destroy(healing_box)

# Input handling
def input(key):
    if key == 'left mouse down':
        shoot()
    elif key == 'r':
        reload()
    elif key == 'escape':
        application.quit()

# Run the game
app.run()
