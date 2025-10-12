import numpy as np
from stl import mesh
import math


def calculate_mass_from_stl(stl_file_path, material_density_g_cm3=1.26):
    """
    Рассчитывает массу 3D-модели из STL-файла.

    Параметры:
        stl_file_path (str): Путь к STL-файлу.
        material_density_g_cm3 (float): Плотность материала в г/см³.
                                        PLA ≈ 1.24, ABS ≈ 1.04, PETG ≈ 1.27

    Возвращает:
        dict: {'volume_cm3': float, 'mass_g': float}
    """
    # Загружаем модель
    your_mesh = mesh.Mesh.from_file(stl_file_path)

    # Вычисляем объём в мм³ (библиотека возвращает в единицах модели, обычно мм)
    volume_mm3 = your_mesh.get_mass_properties()[0]  # volume in mm³

    if volume_mm3 < 0:
        volume_mm3 = -volume_mm3  # STL может быть с "вывернутыми" нормалями

    volume_cm3 = volume_mm3 / 1000.0  # 1 см³ = 1000 мм³

    mass_g = volume_cm3 * material_density_g_cm3

    return mass_g


# # Пример использования:
# if __name__ == "__main__":
#     result = calculate_mass_from_stl("data/stl/направляющая_сервопривода_резака_1.stl", material_density_g_cm3=1.24)
#     print(f"Объём: {result['volume_cm3']} см³")
#     print(f"Масса (PLA): {result['mass_g']} г")