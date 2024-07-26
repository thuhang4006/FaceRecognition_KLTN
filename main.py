import pygame
import time

# Khởi tạo pygame và mixer
pygame.init()
pygame.mixer.init()

# Tải âm thanh WAV
try:
    success_sound = pygame.mixer.Sound('src/sounds/checked.mp3')
    print("Âm thanh đã được tải thành công!")
except pygame.error as e:
    print(f"Lỗi khi tải âm thanh: {e}")

def play_success_sound():
    success_sound.play()
    time.sleep(success_sound.get_length())  # Đợi cho âm thanh phát xong

# Gọi hàm để phát âm thanh
play_success_sound()
