class TreeNode:
    """Clase base para estructurar los datos en un árbol N-ario."""
    def __init__(self, key):
        self.key = key
        self.children = []

    def add_child(self, child_node):
        self.children.append(child_node)

def build_attendance_tree(registros):
    """
    Construye el árbol de asistencias a partir de los registros de la base de datos.
    Estructura:
    UMG - Sede Boca del Monte
        ├── Puerta Principal
        │   └── Persona / Hora
        └── Salones
            ├── Salón 101
            │   └── Persona / Hora
            └── Salón 102
                └── Persona / Hora
    """
    root = TreeNode("UMG - Sede Boca del Monte")
    
    puerta_node = TreeNode("Puerta Principal")
    salones_node = TreeNode("Salones de Clase")
    
    root.add_child(puerta_node)
    root.add_child(salones_node)

    # Diccionario para evitar duplicar el nodo de un mismo salón
    nodos_salones = {}
    
    for ubicacion, nombre, apellido, fecha in registros:
        # Extraer solo la hora de la fecha (puede ser datetime, string YYYY-MM-DD HH:MM:SS, o None)
        if hasattr(fecha, "strftime"):
            hora = fecha.strftime("%H:%M:%S")
        elif isinstance(fecha, str):
            hora = fecha.split(" ")[1] if " " in fecha else fecha
        else:
            fecha_str = str(fecha) if fecha is not None else ""
            hora = fecha_str.split(" ")[1] if " " in fecha_str else fecha_str
        
        persona_str = f"{nombre} {apellido} / {hora}"
        persona_node = TreeNode(persona_str)

        if "puerta" in ubicacion.lower():
            puerta_node.add_child(persona_node)
        else:
            if ubicacion not in nodos_salones:
                nodos_salones[ubicacion] = TreeNode(ubicacion)
                salones_node.add_child(nodos_salones[ubicacion])
            nodos_salones[ubicacion].add_child(persona_node)
            
    return root
