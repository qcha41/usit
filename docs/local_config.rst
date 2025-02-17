.. _localconfig:

Local configuration
===================

To avoid having to provide the full configuration of an instrument (connection type, address, port, slots, etc.) each time to load a **Device**, Autolab proposes storing it locally for further use.

More precisely, this configuration is stored in a local configuration file named ``devices_config.ini``, which is located in the local directory of Autolab. Both this directory and this file are created automatically in your home directory the first time you use the package (the following messages will be displayed, indicating their exact paths).

.. code-block:: none

	The local directory of AUTOLAB has been created: C:\Users\<USER>\autolab.
	It contains the configuration files devices_config.ini, autolab_config.ini and plotter.ini.
	It also contains the 'driver' directory with 'official' and 'local' sub-directories.

.. warning ::

	Do not move or rename the local directory nor the configuration file.

A device configuration is composed of several parameters:

* The name of the device, which is usually the nickname of your instrument in Autolab.
* The name of the associated Autolab **driver**.
* All the connection parameters (connection, address, port, slots, ...)

To see the list of the available device configurations, call the ``list_devices`` function.

.. code-block:: python

	>>> autolab.list_devices()

To know what parameters have to be provided for a particular **Device**, use the `config_help` function with the name of the corresponding driver.

.. code-block:: python

	>>> autolab.config_help('yenista_TUNICS')


Edit the configuration file
---------------------------------

You can manually edit the devices configuration file ``devices_config.ini``.

This file is structured in blocks, each of them containing the configuration of an instrument. Each block contains a header (the configuration name / nickname of the instrument in square brackets ``[ ]``). The parameters and values are then listed below line by line, separated by an equal sign ``=``.

.. code-block:: none

	[<NICKNAME_OF_YOUR_DEVICE>]
	driver = <DRIVER_NAME>
	connection = <CONNECTION_TYPE>
	address = <ADDRESS>
	slot1 = <MODULE_NAME>
	slot1_name = <MY_MODULE_NAME>

To see a concrete example of the block you have to append in the configuration file for a given driver, call the ``config_help`` function with the name of the driver. You can then directly copy and paste this exemple into the configuration file, and customize the value of the parameters to suit those of your instrument. Here is an example for the Yenista Tunics light source:

.. code-block:: none

	[my_tunics]
	driver = yenista_TUNICS
	connection = VISA
	address = GPIB0::2::INSTR

Save the configuration file, and go back to Autolab. You don't need to restart Autolab, the configuration file will be read automatically at the next request.

.. code-block:: python

	>>> laserSource = autolab.get_device('my_tunics')

You can also use Autolab's ``add_device`` function to open up a minimalist graphical interface, allowing you to configure an instrument in a more user-friendly way.

.. code-block:: python

	>>> autolab.add_device()
