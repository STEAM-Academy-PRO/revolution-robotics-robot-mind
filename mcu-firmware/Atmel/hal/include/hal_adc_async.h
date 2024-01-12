/**
 * \file
 *
 * \brief ADC functionality declaration.
 *
 * Copyright (c) 2015-2018 Microchip Technology Inc. and its subsidiaries.
 *
 * \asf_license_start
 *
 * \page License
 *
 * Subject to your compliance with these terms, you may use Microchip
 * software and any derivatives exclusively with Microchip products.
 * It is your responsibility to comply with third party license terms applicable
 * to your use of third party software (including open source software) that
 * may accompany Microchip software.
 *
 * THIS SOFTWARE IS SUPPLIED BY MICROCHIP "AS IS". NO WARRANTIES,
 * WHETHER EXPRESS, IMPLIED OR STATUTORY, APPLY TO THIS SOFTWARE,
 * INCLUDING ANY IMPLIED WARRANTIES OF NON-INFRINGEMENT, MERCHANTABILITY,
 * AND FITNESS FOR A PARTICULAR PURPOSE. IN NO EVENT WILL MICROCHIP BE
 * LIABLE FOR ANY INDIRECT, SPECIAL, PUNITIVE, INCIDENTAL OR CONSEQUENTIAL
 * LOSS, DAMAGE, COST OR EXPENSE OF ANY KIND WHATSOEVER RELATED TO THE
 * SOFTWARE, HOWEVER CAUSED, EVEN IF MICROCHIP HAS BEEN ADVISED OF THE
 * POSSIBILITY OR THE DAMAGES ARE FORESEEABLE.  TO THE FULLEST EXTENT
 * ALLOWED BY LAW, MICROCHIP'S TOTAL LIABILITY ON ALL CLAIMS IN ANY WAY
 * RELATED TO THIS SOFTWARE WILL NOT EXCEED THE AMOUNT OF FEES, IF ANY,
 * THAT YOU HAVE PAID DIRECTLY TO MICROCHIP FOR THIS SOFTWARE.
 *
 * \asf_license_stop
 *
 */

#ifndef HAL_ADC_ASYNC_H_INCLUDED
#define HAL_ADC_ASYNC_H_INCLUDED

#include <hpl_adc_async.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * \addtogroup doc_driver_hal_adc_async
 *
 * @{
 */

/**
 * \brief ADC descriptor
 *
 * The ADC descriptor forward declaration.
 */
struct adc_async_descriptor;

/**
 * \brief ADC callback type
 */
typedef void (*adc_async_cb_t)(const struct adc_async_descriptor *const descr, uint16_t adc_data);

/**
 * \brief ADC callback types
 */
enum adc_async_callback_type {
	/** ADC convert done callback */
	ADC_ASYNC_CONVERT_CB,
	/** ADC monitor callback */
	ADC_ASYNC_MONITOR_CB,
	/** ADC error callback */
	ADC_ASYNC_ERROR_CB
};

/**
 * \brief ADC callbacks
 */
struct adc_async_callbacks {
	/** Monitor callback  */
	adc_async_cb_t monitor;
	/** Error callback  */
	adc_async_cb_t error;
	/** Convert done callback  */
	adc_async_cb_t convert_done;
};

/**
 * \brief ADC descriptor
 */
struct adc_async_descriptor {
	/** ADC device */
	struct _adc_async_device device;
	/** ADC callbacks type */
	struct adc_async_callbacks adc_async_cb;
};

/**
 * \brief Initialize ADC
 *
 * This function initializes the given ADC descriptor.
 * It checks if the given hardware is not initialized and if the given hardware
 * is permitted to be initialized.
 *
 * \param[out] descr         An ADC descriptor to initialize
 * \param[in] hw             The pointer to hardware instance
 *
 * \return Initialization status.
 * \retval -1 Passed parameters were invalid or an ADC is already initialized
 * \retval 0 The initialization is completed successfully
 */
int32_t adc_async_init(struct adc_async_descriptor *const descr, void *const hw);

/**
 * \brief Deinitialize ADC
 *
 * This function deinitializes the given ADC descriptor.
 * It checks if the given hardware is initialized and if the given hardware is
 * permitted to be deinitialized.
 *
 * \param[in] descr An ADC descriptor to deinitialize
 *
 * \return De-initialization status.
 */
int32_t adc_async_deinit(struct adc_async_descriptor *const descr);

/**
 * \brief Enable ADC
 *
 * Use this function to set the ADC peripheral to enabled state.
 *
 * \param[in] descr    Pointer to the ADC descriptor
 *
 * \return Operation status.
 *
 */
int32_t adc_async_enable(struct adc_async_descriptor *const descr);

/**
 * \brief Disable ADC
 *
 * Use this function to set the ADC peripheral to disabled state.
 *
 * \param[in] descr   Pointer to the ADC descriptor
 *
 * \return Operation status.
 *
 */
int32_t adc_async_disable(struct adc_async_descriptor *const descr);

/**
 * \brief Register ADC callback
 *
 * \param[in] io_descr  An adc descriptor
 * \param[in] type      Callback type
 * \param[in] cb        A callback function, passing NULL de-registers callback
 *
 * \return The status of callback assignment.
 * \retval -1 Passed parameters were invalid or the ADC is not initialized
 * \retval 0 A callback is registered successfully
 */
int32_t adc_async_register_callback(struct adc_async_descriptor *const descr, const enum adc_async_callback_type type, adc_async_cb_t cb);

/**
 * \brief Start conversion
 *
 * This function starts single conversion if no automatic (free-run) mode is
 * enabled.
 *
 * \param[in] descr The pointer to the ADC descriptor
 *
 * \return Start conversion status.
 */
int32_t adc_async_start_conversion(struct adc_async_descriptor *const descr);

/**
 * \brief Set ADC reference source
 *
 * This function sets ADC reference source.
 *
 * \param[in] descr     The pointer to the ADC descriptor
 * \param[in] reference A reference source to set
 *
 * \return Status of the ADC reference source setting.
 */
int32_t adc_async_set_reference(struct adc_async_descriptor *const descr, const adc_reference_t reference);

/**
 * \brief Set ADC resolution
 *
 * This function sets ADC resolution.
 *
 * \param[in] descr      The pointer to the ADC descriptor
 * \param[in] resolution A resolution to set
 *
 * \return Status of the ADC resolution setting.
 */
int32_t adc_async_set_resolution(struct adc_async_descriptor *const descr, const adc_resolution_t resolution);

/**
 * \brief Set ADC input source of a channel
 *
 * This function sets the ADC positive and negative input sources.
 *
 * \param[in] descr     The pointer to the ADC descriptor
 * \param[in] pos_input A positive input source to set
 * \param[in] neg_input A negative input source to set
 *
 * \return Status of the ADC channels setting.
 */
int32_t adc_async_set_inputs(struct adc_async_descriptor *const descr, const adc_pos_input_t pos_input,
                             const adc_neg_input_t neg_input);

/**
 * \brief Set ADC conversion mode
 *
 * This function sets ADC conversion mode.
 *
 * \param[in] descr The pointer to the ADC descriptor
 * \param[in] mode  A conversion mode to set
 *
 * \return Status of the ADC conversion mode setting.
 */
int32_t adc_async_set_conversion_mode(struct adc_async_descriptor *const descr, const enum adc_conversion_mode mode);

/**
 * \brief Set ADC differential mode
 *
 * This function sets ADC differential mode.
 *
 * \param[in] descr   The pointer to the ADC descriptor
 * \param[in] mode    A differential mode to set
 *
 * \return Status of the ADC differential mode setting.
 */
int32_t adc_async_set_differential_mode(struct adc_async_descriptor *const descr,
                                                const enum adc_differential_mode mode);

/**
 * \brief Set ADC window mode
 *
 * This function sets ADC window mode.
 *
 * \param[in] descr The pointer to the ADC descriptor
 * \param[in] mode  A window mode to set
 *
 * \return Status of the ADC window mode setting.
 */
int32_t adc_async_set_window_mode(struct adc_async_descriptor *const descr, const adc_window_mode_t mode);

/**
 * \brief Set ADC thresholds
 *
 * This function sets the ADC positive and negative thresholds.
 *
 * \param[in] descr         The pointer to the ADC descriptor
 * \param[in] low_threshold A lower thresholds to set
 * \param[in] up_threshold  An upper thresholds to set
 *
 * \return Status of the ADC thresholds setting.
 */
int32_t adc_async_set_thresholds(struct adc_async_descriptor *const descr, const adc_threshold_t low_threshold,
                                 const adc_threshold_t up_threshold);

/**
 * \brief Retrieve threshold state
 *
 * This function retrieves ADC threshold state.
 *
 * \param[in] descr  The pointer to the ADC descriptor
 * \param[out] state The threshold state
 *
 * \return The state of ADC thresholds state retrieving.
 */
int32_t adc_async_get_threshold_state(const struct adc_async_descriptor *const descr,
                                      adc_threshold_status_t *const            state);

/**
 * \brief Check if conversion is complete
 *
 * This function checks if the ADC has finished the conversion.
 *
 * \param[in] descr   The pointer to the ADC descriptor
 *
 * \return The status of the ADC conversion completion checking.
 * \retval 1 The conversion is complete
 * \retval 0 The conversion is not complete
 */
int32_t adc_async_is_conversion_complete(const struct adc_async_descriptor *const descr);

/**
 * \brief Retrieve the current driver version
 *
 * \return Current driver version.
 */
uint32_t adc_async_get_version(void);
/**@}*/

#ifdef __cplusplus
}
#endif

#include <hpl_missing_features.h>

#endif /* HAL_ADC_ASYNC_H_INCLUDED */
