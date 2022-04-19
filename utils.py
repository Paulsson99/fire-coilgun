def print_data(data: list, units: str, prefix='') -> None:
	data_with_units = [f"{d:.2f} {units}" for d in data]
	print(prefix + ', '.join(data_with_units))