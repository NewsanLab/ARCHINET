
#include "Arduino.h"
#include <string.h>
#include <driver/gpio.h>
#include <driver/spi_slave.h>

#include "SPIS.h"

SPISClass::SPISClass(spi_host_device_t hostDevice, int mosiPin, int misoPin, int sclkPin, int csPin,int readyPin) :
  _hostDevice(hostDevice),
  _mosiPin(mosiPin),
  _misoPin(misoPin),
  _sclkPin(sclkPin),
  _csPin(csPin),
  _readyPin(readyPin) 

{
}
int SPISClass::begin()
{
  spi_bus_config_t busCfg;
  spi_slave_interface_config_t slvCfg;

  pinMode(_readyPin, OUTPUT);
  digitalWrite(_readyPin, HIGH);

  _readySemaphore = xSemaphoreCreateCounting(1, 0);

  attachInterrupt(_csPin, onChipSelect, FALLING);

  memset(&busCfg, 0x00, sizeof(busCfg));
  busCfg.mosi_io_num = _mosiPin;
  busCfg.miso_io_num = _misoPin;
  busCfg.sclk_io_num = _sclkPin;

  memset(&slvCfg, 0x00, sizeof(slvCfg));
  slvCfg.mode = 0;
  slvCfg.spics_io_num = _csPin;
  slvCfg.queue_size = 1; // Configura el tamaño de la cola de transacciones
  slvCfg.flags = 0;
  slvCfg.post_setup_cb = SPISClass::onSetupComplete;
  slvCfg.post_trans_cb = NULL;

  gpio_set_pull_mode((gpio_num_t)_mosiPin, GPIO_FLOATING);
  gpio_set_pull_mode((gpio_num_t)_sclkPin, GPIO_PULLDOWN_ONLY);
  gpio_set_pull_mode((gpio_num_t)_csPin, GPIO_PULLUP_ONLY);

  // Inicializa el bus SPI sin un canal DMA
  spi_slave_initialize(_hostDevice, &busCfg, &slvCfg, 0); // Usar 0 para DMA auto-alloc

  return 1;
}

int SPISClass::transfer(uint8_t out[], uint8_t in[], size_t len)
{
  spi_slave_transaction_t slvTrans;
  spi_slave_transaction_t* slvRetTrans;

  memset(&slvTrans, 0x00, sizeof(slvTrans));

  slvTrans.length = len * 8; // Longitud en bits
  slvTrans.trans_len = 0;///
  slvTrans.tx_buffer = out; // Buffer de datos a enviar
  slvTrans.rx_buffer = in; // Buffer para recibir datos

  spi_slave_queue_trans(_hostDevice, &slvTrans, portMAX_DELAY); // Coloca la transacción en la cola
  xSemaphoreTake(_readySemaphore, portMAX_DELAY); // Espera a que la transacción esté lista
  digitalWrite(_readyPin, LOW);///
  spi_slave_get_trans_result(_hostDevice, &slvRetTrans, portMAX_DELAY); // Obtiene el resultado de la transacción
  digitalWrite(_readyPin, HIGH);///
  return (slvTrans.trans_len / 8); // Retorna la longitud de datos recibidos
}

void SPISClass::onChipSelect()
{
  SPIS.handleOnChipSelect();
}

void SPISClass::handleOnChipSelect()
{
  digitalWrite(_readyPin, HIGH);///
}

void SPISClass::onSetupComplete(spi_slave_transaction_t*)
{
  SPIS.handleSetupComplete();
}

void SPISClass::handleSetupComplete()
{
  xSemaphoreGiveFromISR(_readySemaphore, NULL); // Libera 
}

SPISClass SPIS(HSPI_HOST, 11, 13, 12, 10,48); // MOSI, MISO, SCK, CS,ready
