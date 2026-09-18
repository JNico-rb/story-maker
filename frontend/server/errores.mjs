// Un error que es culpa de la petición, no del servidor.
//
// Existe para que index.mjs no tenga que adivinar por el texto del mensaje si
// algo es un 400 o un 500. Adivinarlo por una expresión regular sobre el
// mensaje funciona hasta que alguien escribe un mensaje nuevo, y entonces un
// error de usuario se convierte en «Error en el servidor».

export class ErrorDeEntrada extends Error {
  constructor(mensaje) {
    super(mensaje)
    this.name = 'ErrorDeEntrada'
  }
}
