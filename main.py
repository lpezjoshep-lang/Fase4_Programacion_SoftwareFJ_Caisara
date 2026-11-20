"""Fase 4 - Sistema Software FJ. Programación orientada a objetos y excepciones."""
from abc import ABC, abstractmethod
from datetime import datetime
import logging

logging.basicConfig(filename='software_fj.log', level=logging.INFO,
                    format='%(asctime)s | %(levelname)s | %(message)s',
                    encoding='utf-8')


class ErrorSistema(Exception):
    """Error controlado de las operaciones de Software FJ."""


class ErrorValidacion(ErrorSistema):
    """Datos inválidos proporcionados por el usuario."""


class ErrorReserva(ErrorSistema):
    """Reserva inválida o cambio de estado no permitido."""


def numero_positivo(valor, nombre):
    """Convierte una entrada a número y exige un valor mayor que cero."""
    try:
        numero = float(valor)
    except (TypeError, ValueError) as exc:
        raise ErrorValidacion(f'{nombre} debe ser numérico') from exc
    if not (0 < numero < float('inf')):
        raise ErrorValidacion(f'{nombre} debe ser positivo y finito')
    return numero


class Entidad(ABC):
    """Entidad general con una descripción obligatoria."""
    @abstractmethod
    def describir(self):
        pass


class Cliente(Entidad):
    """Cliente con nombre y documento encapsulados."""
    def __init__(self, nombre, documento):
        self.nombre = nombre
        self.documento = documento

    @property
    def nombre(self):
        return self.__nombre

    @nombre.setter
    def nombre(self, valor):
        if not isinstance(valor, str) or len(valor.strip()) < 3:
            raise ErrorValidacion('El nombre debe tener al menos 3 caracteres')
        self.__nombre = valor.strip()

    @property
    def documento(self):
        return self.__documento

    @documento.setter
    def documento(self, valor):
        texto = str(valor).strip()
        if not texto.isdigit() or len(texto) < 5:
            raise ErrorValidacion('El documento debe tener al menos 5 dígitos')
        self.__documento = texto

    def describir(self):
        return f'Cliente: {self.nombre} (documento terminado en {self.documento[-3:]})'


class Servicio(Entidad, ABC):
    """Contrato de servicios: validación, costo y descripción."""
    def __init__(self, codigo, tarifa):
        if not isinstance(codigo, str) or not codigo.strip():
            raise ErrorValidacion('El código del servicio es obligatorio')
        self.codigo = codigo.strip()
        self.tarifa = numero_positivo(tarifa, 'La tarifa')
        self.disponible = True

    @abstractmethod
    def validar_parametros(self):
        pass

    @abstractmethod
    def calcular_costo(self, duracion, impuesto=0, descuento=0):
        """Parámetros opcionales permiten variantes de cálculo."""
        pass

    def aplicar_ajustes(self, base, impuesto, descuento):
        impuesto = float(impuesto)
        descuento = float(descuento)
        if not (0 <= impuesto <= 100 and 0 <= descuento <= 100):
            raise ErrorValidacion('Impuesto y descuento deben estar entre 0 y 100')
        return round(base * (1 - descuento / 100) * (1 + impuesto / 100), 2)


class Sala(Servicio):
    """Alquiler de sala con capacidad definida."""
    def __init__(self, codigo, tarifa, capacidad):
        super().__init__(codigo, tarifa)
        self.capacidad = capacidad
        self.validar_parametros()

    def validar_parametros(self):
        if not isinstance(self.capacidad, int) or self.capacidad <= 0:
            raise ErrorValidacion('La capacidad de la sala debe ser un entero positivo')

    def calcular_costo(self, duracion, impuesto=0, descuento=0):
        return self.aplicar_ajustes(self.tarifa * numero_positivo(duracion, 'Duración'), impuesto, descuento)

    def describir(self):
        return f'Sala {self.codigo}, capacidad {self.capacidad}, tarifa {self.tarifa}/hora'


class Equipo(Servicio):
    """Alquiler de equipos por horas."""
    def __init__(self, codigo, tarifa, tipo):
        super().__init__(codigo, tarifa)
        self.tipo = tipo
        self.validar_parametros()

    def validar_parametros(self):
        if not isinstance(self.tipo, str) or not self.tipo.strip():
            raise ErrorValidacion('El tipo de equipo es obligatorio')

    def calcular_costo(self, duracion, impuesto=0, descuento=0):
        return self.aplicar_ajustes(self.tarifa * numero_positivo(duracion, 'Duración'), impuesto, descuento)

    def describir(self):
        return f'Equipo {self.codigo}, tipo {self.tipo}, tarifa {self.tarifa}/hora'


class Asesoria(Servicio):
    """Asesoría especializada por horas."""
    def __init__(self, codigo, tarifa, especialidad):
        super().__init__(codigo, tarifa)
        self.especialidad = especialidad
        self.validar_parametros()

    def validar_parametros(self):
        if not isinstance(self.especialidad, str) or not self.especialidad.strip():
            raise ErrorValidacion('La especialidad es obligatoria')

    def calcular_costo(self, duracion, impuesto=0, descuento=0):
        return self.aplicar_ajustes(self.tarifa * numero_positivo(duracion, 'Duración'), impuesto, descuento)

    def describir(self):
        return f'Asesoría {self.codigo}, especialidad {self.especialidad}, tarifa {self.tarifa}/hora'


class Reserva(Entidad):
    """Relaciona cliente, servicio, duración y estado."""
    def __init__(self, cliente, servicio, duracion):
        if not isinstance(cliente, Cliente) or not isinstance(servicio, Servicio):
            raise ErrorReserva('La reserva requiere un cliente y un servicio válidos')
        self.cliente = cliente
        self.servicio = servicio
        self.duracion = numero_positivo(duracion, 'Duración')
        self.estado = 'PENDIENTE'

    def confirmar(self):
        if self.estado != 'PENDIENTE':
            raise ErrorReserva('Solo se pueden confirmar reservas pendientes')
        if not self.servicio.disponible:
            raise ErrorReserva('El servicio no está disponible')
        self.estado = 'CONFIRMADA'
        logging.info('Reserva confirmada: %s', self.servicio.codigo)

    def cancelar(self):
        if self.estado == 'CANCELADA':
            raise ErrorReserva('La reserva ya estaba cancelada')
        self.estado = 'CANCELADA'
        logging.info('Reserva cancelada: %s', self.servicio.codigo)

    def procesar(self, impuesto=0, descuento=0):
        try:
            if self.estado != 'CONFIRMADA':
                raise ErrorReserva('Solo se procesan reservas confirmadas')
            total = self.servicio.calcular_costo(self.duracion, impuesto, descuento)
        except ErrorSistema:
            logging.exception('Fallo al procesar la reserva')
            raise
        else:
            logging.info('Reserva procesada por %.2f', total)
            return total
        finally:
            logging.info('Finalizó el intento de procesamiento')

    def describir(self):
        return f'Reserva {self.estado}: {self.cliente.nombre}, {self.servicio.codigo}, {self.duracion} horas'


class SistemaSoftwareFJ:
    """Administra objetos en listas y no utiliza bases de datos."""
    def __init__(self):
        self.clientes = []
        self.servicios = []
        self.reservas = []

    def registrar_cliente(self, nombre, documento):
        cliente = Cliente(nombre, documento)
        if any(c.documento == cliente.documento for c in self.clientes):
            raise ErrorValidacion('El documento ya está registrado')
        self.clientes.append(cliente)
        logging.info('Cliente registrado: documento terminado en %s', cliente.documento[-3:])
        return cliente

    def agregar_servicio(self, servicio):
        if not isinstance(servicio, Servicio):
            raise ErrorValidacion('Se requiere un servicio válido')
        if any(s.codigo == servicio.codigo for s in self.servicios):
            raise ErrorValidacion('Código de servicio repetido')
        self.servicios.append(servicio)
        logging.info('Servicio agregado: %s', servicio.codigo)
        return servicio

    def crear_reserva(self, cliente, servicio, duracion):
        if cliente not in self.clientes or servicio not in self.servicios:
            raise ErrorReserva('Cliente o servicio no registrado')
        reserva = Reserva(cliente, servicio, duracion)
        self.reservas.append(reserva)
        logging.info('Reserva creada para %s', servicio.codigo)
        return reserva


def ejecutar_prueba(numero, descripcion, operacion, espera_error=False):
    """Ejecuta una prueba sin detener las siguientes ante un error."""
    try:
        resultado = operacion()
    except Exception as exc:
        logging.exception('Prueba %s: %s', numero, descripcion)
        if espera_error and isinstance(exc, ErrorSistema):
            print(f'{numero:02}. CORRECTO (error controlado) | {descripcion}: {exc}')
            return True
        print(f'{numero:02}. FALLÓ | {descripcion}: {exc}')
        return False
    else:
        if espera_error:
            print(f'{numero:02}. FALLÓ (faltó validar) | {descripcion}')
            return False
        print(f'{numero:02}. CORRECTO | {descripcion}: {resultado}')
        return True
    finally:
        logging.info('Prueba %s finalizada', numero)


def demostracion():
    """Simula 15 operaciones, incluyendo casos exitosos y fallidos."""
    sistema = SistemaSoftwareFJ()
    datos = {}
    pruebas = [
        ('Registrar cliente válido', lambda: datos.setdefault('cliente', sistema.registrar_cliente('Ana Torres', '12345678')), False),
        ('Rechazar nombre vacío', lambda: sistema.registrar_cliente('', '98765432'), True),
        ('Rechazar documento duplicado', lambda: sistema.registrar_cliente('Luis Pérez', '12345678'), True),
        ('Crear servicio sala', lambda: datos.setdefault('sala', sistema.agregar_servicio(Sala('S01', 50000, 20))), False),
        ('Rechazar sala sin capacidad', lambda: sistema.agregar_servicio(Sala('S02', 50000, 0)), True),
        ('Crear servicio equipo', lambda: datos.setdefault('equipo', sistema.agregar_servicio(Equipo('E01', 30000, 'Portátil'))), False),
        ('Crear servicio asesoría', lambda: datos.setdefault('asesoria', sistema.agregar_servicio(Asesoria('A01', 80000, 'Python'))), False),
        ('Rechazar tarifa negativa', lambda: sistema.agregar_servicio(Equipo('E02', -100, 'Proyector')), True),
        ('Crear reserva válida', lambda: datos.setdefault('reserva', sistema.crear_reserva(datos['cliente'], datos['sala'], 2)), False),
        ('Confirmar reserva', lambda: datos['reserva'].confirmar() or datos['reserva'].estado, False),
        ('Procesar reserva con impuesto', lambda: datos['reserva'].procesar(impuesto=19), False),
        ('Rechazar reserva con duración inválida', lambda: sistema.crear_reserva(datos['cliente'], datos['equipo'], -2), True),
        ('Rechazar reserva de servicio no disponible', lambda: probar_no_disponible(sistema, datos), True),
        ('Cancelar reserva', lambda: datos['reserva'].cancelar() or datos['reserva'].estado, False),
        ('Rechazar procesamiento de reserva cancelada', lambda: datos['reserva'].procesar(), True),
    ]
    print('SOFTWARE FJ | DEMOSTRACIÓN DE 15 OPERACIONES')
    print('Fecha y hora:', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print('-' * 72)
    aprobadas = sum(ejecutar_prueba(i, nombre, funcion, error)
                    for i, (nombre, funcion, error) in enumerate(pruebas, 1))
    print('-' * 72)
    print(f'Resultado: {aprobadas}/{len(pruebas)} pruebas correctas')
    print(f'Objetos almacenados: {len(sistema.clientes)} clientes, '
          f'{len(sistema.servicios)} servicios, {len(sistema.reservas)} reservas')
    print('Registro de eventos y errores: software_fj.log')


def probar_no_disponible(sistema, datos):
    """Intenta confirmar una reserva de un servicio no disponible."""
    servicio = datos['asesoria']
    servicio.disponible = False
    reserva = sistema.crear_reserva(datos['cliente'], servicio, 1)
    reserva.confirmar()


if __name__ == '__main__':
    demostracion()
