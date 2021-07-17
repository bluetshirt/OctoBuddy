# coding=utf-8
from __future__ import absolute_import, unicode_literals

import octoprint.plugin
import RPi.GPIO as GPIO

import os

class OctoBuddyPlugin(octoprint.plugin.StartupPlugin,
                      octoprint.plugin.ShutdownPlugin,
                      octoprint.plugin.SettingsPlugin,
                      octoprint.plugin.TemplatePlugin):

    def on_after_startup(self):
        self._logger.info("OctoBuddy %s Alive Now!", self._plugin_version)
        self._logger.info(self._printer.get_state_id())
        self._logger.info(GPIO.RPI_INFO)
        self.setup_GPIO()

    def set_temps(self, tool_temp, bed_temp):      
    
        nozzle_temp_formatted = str(tool_temp).rjust(3)
        nozzle_string = f"Nozzle->{nozzle_temp_formatted}"

        bed_temp_formatted = str(bed_temp).rjust(3)
        bed_string = f"Bed->{bed_temp_formatted}"
                            
        self._printer.commands("M117 {nozzle_string}  {bed_string}")
        self._printer.set_temperature("tool0", tool_temp)
        self._printer.set_temperature("bed", bed_temp)
        self._logger.info("Set Nozzle to {tool_temp}, Bed to {bed_temp}.")

    def button_callback(self, channel):

        if channel == self.pause_pin:
            elif self._printer.get_state_id() == "PRINTING" or self._printer.is_printing():
                self._printer.pause_print
            if self._printer.get_state_id() == "PAUSED" or self._printer.is_pausing(): 
                self._printer.resume_print
                            
        if self._printer.get_state_id() != "PRINTING" and self._printer.is_printing() == False:
            if channel == self.home_pin:
                self._printer.home("x")
                self._printer.home("y")
                self._printer.home("z")

            if channel == self.heat_lo_pin:
                self.set_temps(self.lo_nozzle_temp, self.lo_bed_temp)
            if channel == self.heat_hi_pin: 
                self.set_temps(self.hi_nozzle_temp, self.hi_bed_temp)
            if channel == self.heat_off_pin: 
                self.set_temps(0, 0)    
            if channel == self.print_on_demand_pin:
                self.select_file(script_path, True, printAfterSelect=True)

    def setup_GPIO(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        
        self.SetupSingleGPIO(self.heat_lo_pin)
        self.SetupSingleGPIO(self.heat_hi_pin)
        self.SetupSingleGPIO(self.heat_off_pin)
        self.SetupSingleGPIO(self.pause_pin)
        self.SetupSingleGPIO(self.home_pin)
        self.SetupSingleGPIO(self.print_on_demand_pin)

    def get_settings_defaults(self): 
        return dict(
            heat_lo_pin   = 31,
            heat_hi_pin   = 33,
            heat_off_pin  = 35,
            pause_pin    = 19,   
            home_pin     = 21,
            print_on_demand_pin = 23,
            lo_nozzle_temp = 200,
            lo_bed_temp = 50,
            hi_nozzle_temp = 210,
            hi_bed_temp = 60,
            script_path = "PrintOnDemand.gcode",
            debounce    = 400
        )

    def get_template_configs(self):
        return [dict(type = "settings", custom_bindings=False)]

    def on_settings_save(self, data):
        self.RemoveEventDetects(); #remove all active event detects
        GPIO.cleanup()
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self._logger.info("OctoBuddy settings changed, updating GPIO setup")

        self.setup_GPIO()

    def SetupSingleGPIO(self, channel):
        try:
            if channel != -1:
                GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
                GPIO.add_event_detect(channel, GPIO.RISING, callback=self.button_callback, bouncetime = self.debounce)
                self._logger.info("New Event Detect has been added to GPIO # %s", channel)

        except:
            self._logger.exception("Cannot setup GPIO ports %s, check to makes sure you don't have the same ports assigned to multiple actions", str(channel))

    def RemoveEventDetects(self): #4
        try:
            if self.home_pin != -1:
                GPIO.remove_event_detect(self.home_pin)
            if self.pause_pin != -1:
                GPIO.remove_event_detect(self.pause_pin)
            if self.print_on_demand_pin != -1:
                GPIO.remove_event_detect(self.print_on_demand_pin)         
            if self.heat_lo_pin != -1:
                GPIO.remove_event_detect(self.heat_lo_pin)
            if self.heat_hi_pin != -1:
                GPIO.remove_event_detect(self.heat_hi_pin)
            if self.heat_off_pin != -1:
                GPIO.remove_event_detect(self.heat_off_pin)
        except:
            self._logger.info("Issue with removing event detects.  Contact plugin owner")

    def on_shutdown(self):
        GPIO.cleanup()
        self._logger.info("OctoBuddy Going to Bed Now!")

    @property
    def debounce(self):
        return int(self._settings.get(["debounce"]))

    @property
    def home_pin(self):
        return int(self._settings.get(["home_pin"]))

    @property
    def pause_pin(self):
        return int(self._settings.get(["pause_pin"]))

    @property
    def print_on_demand_pin(self):
        return int(self._settings.get(["print_on_demand_pin"]))

    @property
    def heat_hi_pin(self):
        return int(self._settings.get(["heat_hi_pin"]))

    @property
    def heat_lo_pin(self):
        return int(self._settings.get(["heat_lo_pin"]))

    @property
    def heat_off_pin(self):
        return int(self._settings.get(["heat_off_pin"]))

    @property
    def lo_nozzle_temp(self):
        return int(self._settings.get(["lo_nozzle_temp"]))

    @property
    def lo_bed_temp(self):
        return int(self._settings.get(["lo_bed_temp"]))
        
    @property
    def hi_nozzle_temp(self):
        return int(self._settings.get(["hi_nozzle_temp"]))

    @property
    def hi_bed_temp(self):
        return int(self._settings.get(["hi_bed_temp"]))

    @property
    def script_path(self):
        return int(self._settings.get(["script_path"]))


    def get_update_information(self):
        return dict(
            OctoBuddy=dict(
                displayName=self._plugin_name,
                displayVersion=self._plugin_version,
                type="github_release",
                current=self._plugin_version,
                user="bluetshirt",
                repo="OctoBuddy",

                pip="https://github.com/bluetshirt/OctoBuddy/archive/{target_version}.zip"
            )
        )

__plugin_pythoncompat__ = ">=2.7,<4"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = OctoBuddyPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
