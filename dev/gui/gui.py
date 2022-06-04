import os

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.filechooser import FileChooser
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.floatlayout import MDFloatLayout

from dev_database_handler import GUIDatabase
from gamblers import GAMBLER_ID_DICT
from model import Model
from salty_bet_driver import SaltyBetGuiDriver

KIVY_FILE_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "kv_files")


class MainScreen(MDBoxLayout):
    def __init__(self, driver: SaltyBetGuiDriver, **kwargs):
        super().__init__(**kwargs)
        self.driver = driver
        self.database = GUIDatabase()

        # Set up the GUI
        self.orientation = "horizontal"
        self.left_panel = Builder.load_file(os.path.join(KIVY_FILE_PATH, "main_left.kv"))
        self.left_panel.ids.balance_label.text = f"Balance: ${driver.get_current_balance():,}"
        self.add_widget(self.left_panel)
        self.__init_right_panel()

        # todo Prompt the user to select a model to load
        # model =

        # todo: Change these to be user selectable from the toolbar
        self.model = Model("02.32.56_model_before_temp_scaling")
        self.gambler = GAMBLER_ID_DICT[3]

        # Set up the state machine
        self.last_state = self.driver.STATE_DICT["START"]
        self.state_machine_event = Clock.schedule_interval(self.state_machine_manager, 5)

    def __draw_shadow__(self, origin, end, context=None):
        pass

    def __init_right_panel(self):
        """
        Initializes the right panel with a graph of the players balance over time
        :return:
        """
        self.graph_screen = MDFloatLayout()
        self.add_widget(self.graph_screen)

    def state_machine_manager(self):
        current_state = self.driver.get_current_state()

        # Don't do anything if the state hasn't changed
        if self.last_state == current_state:
            return

        # Wait for a new match to start
        if self.last_state == self.driver.STATE_DICT["START"] and current_state != self.driver.STATE_DICT["BETS_OPEN"]:
            return

        # Update the GUI
        if current_state == self.driver.STATE_DICT["BETS_OPEN"]:
            self.update_match_info()
        elif current_state == self.driver.STATE_DICT["BETS_CLOSED"]:
            self.update_odds()
        elif current_state == self.driver.STATE_DICT["PAYOUT"]:
            self.update_payout()

        self.last_state = current_state

    def update_match_info(self):
        """
        Sets the current fighters and their predicted odds
        :return:
        """

        # Update with the current balance
        if self.driver.is_tournament():
            # Update balance display, change color to purple
            balance = self.driver.get_current_balance()
            self.left_panel.ids.balance_label.text = f"Balance: ${balance:,}"
            self.left_panel.ids.balance_label.color = [0.5, 0, 0.5, 1]

            # todo: Reset graph to display only results from this tournament
        else:
            balance = self.driver.get_current_balance()
            self.left_panel.ids.balance_label.text = f"Balance: ${balance:,}"
            self.left_panel.ids.balance_label.color = [0, 1, 0, 1]

            # todo: Update the graph

        # Update Fighters
        red, blue = self.driver.get_current_matchup()
        self.left_panel.ids.red_team.text = red
        self.left_panel.ids.blue_team.text = blue

        # Update Confidence
        red_conf, blue_conf = self.model.predict_match(red, blue)
        self.left_panel.ids.red_conf_bar.value = red_conf
        self.left_panel.ids.blue_conf_bar.value = blue_conf
        self.left_panel.ids.red_conf_label.text = f"{red_conf:.2%}"
        self.left_panel.ids.blue_conf_label.text = f"{blue_conf:.2%}"

        # Place bet and display bet amount
        bet_amount = self.gambler.get_bet_amount(balance, max(red_conf, blue_conf))
        self.left_panel.ids.bet_amount_label.text = f"Bet Amount: ${bet_amount:,}"

        # Update match count
        self.left_panel.ids.matchup_count_label.text = f"Matchup Count: {self.database.get_matchup_count(red, blue)}"

        # Wipe old information
        self.left_panel.ids.red_odds_bar.value = 0
        self.left_panel.ids.blue_odds_bar.value = 0
        self.left_panel.ids.red_odds_label.text = "--.--%"
        self.left_panel.ids.blue_odds_label.text = "--.--%"
        self.left_panel.ids.red_pot.text = "$-,---,---"
        self.left_panel.ids.blue_pot.text = "$-,---,---"
        self.left_panel.ids.winner_label.text = ""
        self.left_panel.ids.payout_label.text = ""
        self.left_panel.ids.startup_label.text = ""

    def update_odds(self):
        """
        Updates the odds and pots
        :return:
        """
        red_odds, blue_odds = self.driver.get_current_odds()
        red_pot, blue_pot = self.driver.get_current_pots()

        # Translate odds to percentages
        percent_min = min(red_odds, blue_odds) / max(red_odds, blue_odds)
        percent_max = 1 - percent_min
        red_odds = percent_max if red_pot > blue_pot else percent_min
        blue_odds = percent_max if blue_pot > red_pot else percent_min

        # Update odds and pots
        self.left_panel.ids.red_odds_bar.value = red_odds
        self.left_panel.ids.blue_odds_bar.value = blue_odds
        self.left_panel.ids.red_odds_label.text = f"{red_odds:.2%}"
        self.left_panel.ids.blue_odds_label.text = f"{blue_odds:.2%}"
        self.left_panel.ids.red_pot.text = f"${red_pot:,}"
        self.left_panel.ids.blue_pot.text = f"${blue_pot:,}"

    def update_payout(self):
        # Display the winner
        winner = self.driver.get_winner()
        self.left_panel.ids.winner_label.text = f"{winner.capitalize()} Team Wins!"
        self.left_panel.ids.winner_label.color = [1, 0, 0, 1] if winner == "red" else [0, 0, 1, 1]

        # Display the payout
        payout = self.driver.get_payout()
        self.left_panel.ids.payout_label.text = f"Winnings: {'+' if payout > 0 else '-'}${payout:,}"
        self.left_panel.ids.payout_label.color = [0, 1, 0, 1] if payout > 0 else [1, 0, 0, 1]

        # todo: update graph, model accuracy, balance, profit, ect.


def spawn_login_error_popup():
    dialog = MDDialog(
        title="Login Failed",
        text="Please check your username and password and try again.",
        type="alert",
        size_hint=(.6, .5),
        buttons=[
            MDFlatButton(
                text="Close",
                on_release=lambda x: dialog.dismiss()
            )
        ]
    )
    dialog.open()


# todo fix this shit
def select_file_script():
    file_path = FileChooser().open()
    if file_path is None:
        return
    return file_path


def spawn_model_selection_popup():
    dialog = MDDialog(
        title="Login Successful",
        text="Please select a model to use for betting.",
        type="alert",
        size_hint=(.6, .5),
        buttons=[
            MDFlatButton(
                text="Select Model",
                on_release=select_file_script
            ),
            MDFlatButton(
                text="Close",
                on_release=lambda x: dialog.dismiss()
            )
        ]
    )
    dialog.open()

    return


class SaltyBetAIApp(MDApp):
    def __init__(self):
        super().__init__()
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepPurple"
        self.driver = SaltyBetGuiDriver()

    def login(self, username, password):
        if self.driver.login(username, password):  # Successful login
            # remove login screen
            self.root.clear_widgets()

            # resize window to better fit app
            initial_center = Window.center
            px = 75
            Window.size = 20 * px, 10 * px
            Window.left = Window.center[0] - initial_center[0] / 2
            Window.top = Window.center[1] - initial_center[1] / 2

            # switch to the main screen
            self.root.add_widget(MainScreen(self.driver))

        else:  # Login failed, display error message and clear login fields
            spawn_login_error_popup()
            self.root.ids.username_field.text = ""
            self.root.ids.password_field.text = ""

    def build(self):
        return Builder.load_file(os.path.join(KIVY_FILE_PATH, "login.kv"))


if __name__ == '__main__':
    SaltyBetAIApp().run()
