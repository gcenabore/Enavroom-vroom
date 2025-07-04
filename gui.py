from tkinter import Tk
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
from bookingsystem import Booking, BookingSystem, get_distance, LOCATIONS, DISTANCE_MATRIX, ROUTE_IMAGE_MAP 

PURPLE_DARK = "#360042"
HIGHLIGHT_COLOR = "#6A0DAD"
GRAY_LIGHT = "#F0F0F0"
WHITE = "#FFFFFF"
TEXT_COLOR = "#333333"
RED_COLOR = "#FF0000"
GREEN_COLOR = "#008000"

FONT_TITLE = ("Arial", 12, "bold")
FONT_SUBTITLE = ("Arial", 8, "bold")
FONT_NORMAL = ("Arial", 7)
FONT_PRICE = ("Arial", 12, "bold")
FONT_BUTTON = ("Arial", 10, "bold")
FONT_HEADER = ("Arial", 18, "bold") # For page titles
FONT_BODY = ("Arial", 10)

_image_references = {}


IMAGE_BASE_PATH = os.path.join(os.path.expanduser('~'), 'enavroom_assets')

def load_image(filename, size=None, is_circular=False, fill_color=(200, 200, 200)):
    """
    Loads an image, optionally resizes it, and can make it circular.
    Uses a global dictionary to keep references.
    Provides a placeholder if the image is not found or fails to load.
    """
    filepath = os.path.join(IMAGE_BASE_PATH, filename)
    img_key = f"{filepath}_{size[0]}x{size[1]}_{is_circular}" if size else f"{filepath}_{is_circular}"

    if img_key in _image_references:
        return _image_references[img_key]

    pil_img = None
    try:
        if os.path.exists(filepath):
            pil_img = Image.open(filepath)
            if size:
                pil_img = pil_img.resize(size, Image.LANCZOS)
        else:
            print(f"DEBUG: Image file not found: {filepath}. Creating placeholder.")
            raise FileNotFoundError # Trigger fallback to placeholder creation

        if is_circular:
            # Create a circular image
            mask = Image.new('L', pil_img.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + pil_img.size, fill=255)
            # Apply mask to the image, assuming RGBA for transparency
            if pil_img.mode != 'RGBA':
                pil_img = pil_img.convert('RGBA')
            pil_img.putalpha(mask)

    except (FileNotFoundError, Exception) as e:
        # print(f"ERROR: Could not load or process image {filepath}: {e}. Creating fallback placeholder.")
        if size is None: size = (50, 50) # Default size for placeholder if not provided
        pil_img = Image.new('RGB', size, fill_color)
        d = ImageDraw.Draw(pil_img)
        try:
            font = ImageFont.truetype("arial.ttf", int(size[1] * 0.3))
        except IOError:
            font = ImageFont.load_default()

        text = filename.split('.')[0]
        if len(text) > 10: text = text[:7] + "..."
        try:
            bbox = d.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except AttributeError: # Fallback for older Pillow versions
            text_width, text_height = d.textsize(text, font=font)

        x = (size[0] - text_width) / 2
        y = (size[1] - text_height) / 2
        d.text((x, y), text, fill=(0,0,0), font=font)

    if pil_img:
        photo = ImageTk.PhotoImage(pil_img)
        _image_references[img_key] = photo
        return photo
    return None # Should not happen if placeholder is created

# --- Main Application Class ---

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Enavroom App")
        self.geometry("375x667") # Typical mobile app size
        self.resizable(False, False)
        self.configure(bg=PURPLE_DARK)

        self.frames = {}
        self.booking_system = BookingSystem("bookings.json")  # Initialize booking system with file
        self.booking_system.load() # Load existing bookings from file

        
        # State variables to pass data between pages
        self.current_booking_details = {
            "vehicle_type": "",
            "pickup_location": "",
            "dropoff_location": "",
            "distance": 0,
            "cost": 0,
            "payment_method": "Cash",
            "booking_id": None
        }

        # Create container frame for all pages
        container = tk.Frame(self, bg=PURPLE_DARK)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Initialize all pages and store them in self.frames
        for F in (StartPage, HomePage, MessagePage, NotificationPage, HistoryPage, PUandDOPage, MapPage,
                  LoadingPage, WeFoundDriverEnacarPage, WeFoundDriverEnavroomPage, DonePage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage") # Start with the StartPage

    def show_frame(self, page_name):
        """Shows a frame for the given page name and updates its content if needed."""
        frame = self.frames[page_name]
        # Call an update method on the frame if it exists and is needed
        if hasattr(frame, 'on_show'):
            frame.on_show()
        frame.tkraise()
        print(f"DEBUG: Showing frame: {page_name}")

    def exit_app(self):
        """Prompts user and exits the application."""
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.booking_system.save()
            self.destroy()

    def update_booking_details(self, **kwargs):
        """Updates the current booking details dictionary."""
        self.current_booking_details.update(kwargs)
        print(f"DEBUG: Booking details updated: {self.current_booking_details}")

# --- Common Helper for Binding Widgets Recursively ---
def bind_widgets_recursively(widget, func):
    """Binds a function to a widget and all its children."""
    widget.bind("<Button-1>", func)
    for child in widget.winfo_children():
        bind_widgets_recursively(child, func)

class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=PURPLE_DARK)

        # Enavroom Logo
        logo_img_size = (250, 80)
        logo_img = load_image("logo_enavroom.png", size=logo_img_size)

        if logo_img:
            logo_label = tk.Label(self, image=logo_img, bg=PURPLE_DARK)
            logo_label.image = logo_img
            logo_label.place(relx=0.5, rely=0.35, anchor=tk.CENTER)
        else:
            tk.Label(self, text="ENAVROOM", font=("Arial", 28, "bold"), bg=PURPLE_DARK, fg=WHITE).place(relx=0.5, rely=0.35, anchor=tk.CENTER)

        # Start Button
        start_button = tk.Button(self, text="Start", font=FONT_BUTTON,
                                 command=lambda: controller.show_frame("HomePage"),
                                 bg=WHITE, fg=TEXT_COLOR,
                                 width=15, height=2,
                                 relief="flat", bd=0, cursor="hand2",
                                 highlightbackground=GRAY_LIGHT,
                                 highlightthickness=1,
                                 border=0,
                                 overrelief="raised")
        start_button.place(relx=0.5, rely=0.65, anchor=tk.CENTER)

        # Exit Button
        exit_button = tk.Button(self, text="Exit", font=FONT_BUTTON,
        command=controller.exit_app,
        bg=WHITE, fg=TEXT_COLOR,
        width=15, height=2,
        relief="flat", bd=0, cursor="hand2",
        highlightbackground=GRAY_LIGHT,
        highlightthickness=1,
        border=0,
        overrelief="raised")
        exit_button.place(relx=0.5, rely=0.75, anchor=tk.CENTER)

class HomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=GRAY_LIGHT)

        # --- Top Header Frame ---
        header_frame = tk.Frame(self, bg=PURPLE_DARK, height=100)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)

        logo_header_img = load_image("logo_enavroom.png", (250, 80))
        if logo_header_img:
            logo_label = tk.Label(header_frame, image=logo_header_img, bg=PURPLE_DARK, bd=0, relief="flat")
            logo_label.image = logo_header_img
            logo_label.pack(pady=10)
        else:
            tk.Label(header_frame, text="ENNAVROOM", font=("Arial", 28, "bold"), fg=WHITE, bg=PURPLE_DARK).pack(pady=10)

        # --- Main Content Area Frame ---
        content_frame_homepage = tk.Frame(self, bg=GRAY_LIGHT)
        content_frame_homepage.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Service Selection Icons
        service_icons_frame = tk.Frame(content_frame_homepage, bg=WHITE, relief="solid", bd=1)
        service_icons_frame.pack(pady=20, padx=20, fill=tk.X)

        def create_service_button(parent, filename, text, vehicle_type_data=None):
            tk_icon = load_image(filename, size=(60, 60), is_circular=True, fill_color=PURPLE_DARK)
            button_frame = tk.Frame(parent, bg=WHITE)

            if tk_icon:
                icon_label = tk.Label(button_frame, image=tk_icon, bg=WHITE, cursor="hand2")
                icon_label.image = tk_icon
                icon_label.pack(pady=(10, 5))
            else:
                icon_label = tk.Label(button_frame, text=text[0], font=("Arial", 20, "bold"),
                                      bg=PURPLE_DARK, fg=WHITE, width=3, height=2,
                                      relief="solid", bd=1, cursor="hand2")
                icon_label.pack(pady=(10, 5))

            text_label = tk.Label(button_frame, text=text, font=("Arial", 12), fg=TEXT_COLOR, bg=WHITE, cursor="hand2")
            text_label.pack(pady=(0, 10))

            def command_wrapper(event):
                if vehicle_type_data:
                    self.controller.update_booking_details(vehicle_type=vehicle_type_data)
                self.controller.show_frame("PUandDOPage")

            bind_widgets_recursively(button_frame, command_wrapper)
            return button_frame

        # Moto Taxi Button
        moto_taxi_button_frame = create_service_button(service_icons_frame, "moto_taxi.png", "Moto Taxi", "Enavroom-vroom")
        moto_taxi_button_frame.pack(side=tk.LEFT, expand=True, padx=15, pady=10)

        # Car Button (default to 4-seater)
        car_button_frame = create_service_button(service_icons_frame, "car.png", "Car", "Car (4-seater)")
        car_button_frame.pack(side=tk.LEFT, expand=True, padx=15, pady=10)

        # --- Bottom Navigation Bar Frame ---
        nav_frame = tk.Frame(self, bg=WHITE, height=70, bd=1, relief=tk.RAISED)
        nav_frame.pack(fill=tk.X, side=tk.BOTTOM)
        nav_frame.pack_propagate(False)

        nav_buttons_container = tk.Frame(nav_frame, bg=WHITE)
        nav_buttons_container.pack(expand=True)

        def create_nav_button(parent, filename, text, command):
            tk_icon = load_image(filename, size=(30, 30))
            if tk_icon:
                button = tk.Button(parent, image=tk_icon, text=text, compound=tk.TOP,
                                   font=("Arial", 10), fg=TEXT_COLOR, bg="white",
                                   command=command, bd=0, relief=tk.FLAT,
                                   activebackground=GRAY_LIGHT, activeforeground=PURPLE_DARK,
                                   cursor="hand2")
                button.image = tk_icon
                return button
            return None

        home_button = create_nav_button(nav_buttons_container, "home.png", "HOME", lambda: messagebox.showinfo("Navigation", "Already on Home Page!"))
        if home_button:
            home_button.pack(side=tk.LEFT, padx=20)

        messages_button = create_nav_button(nav_buttons_container, "message.png", "MESSAGES", lambda: controller.show_frame("MessagePage"))
        if messages_button:
            messages_button.pack(side=tk.LEFT, padx=20)

        history_button = create_nav_button(nav_buttons_container, "history.png", "HISTORY", lambda: controller.show_frame("HistoryPage"))
        if history_button:
            history_button.pack(side=tk.LEFT, padx=20)

        exit_button = tk.Button(
            self, text="Exit App",
            font=FONT_BUTTON,
            command=controller.destroy,
            bg="#470366", fg=WHITE,
            padx=20, pady=10,
            relief="raised", bd=0,
            cursor="hand2"
        )
        exit_button.pack(pady=(10, 20))

class MessagePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=GRAY_LIGHT)

        self._create_header("Messages", lambda: controller.show_frame("HomePage"))

        tk.Label(self, text="You have no new messages.", font=FONT_BODY, bg=GRAY_LIGHT, fg=TEXT_COLOR).pack(pady=50)

        tk.Button(self, text="View Notifications", font=FONT_BUTTON,
                  command=lambda: controller.show_frame("NotificationPage"),
                  bg=PURPLE_DARK, fg=WHITE, padx=20, pady=10).pack(pady=10)

    def _create_header(self, title, back_command):
        header_frame = tk.Frame(self, bg=PURPLE_DARK, height=50)
        header_frame.pack(fill="x", pady=(0,0))
        header_frame.pack_propagate(False)

        back_button_img = load_image("arrow.png", (25, 25))
        if back_button_img:
            back_button = tk.Button(header_frame, image=back_button_img, command=back_command, bd=0, bg=header_frame.cget("bg"), cursor="hand2")
            back_button.image = back_button_img
            back_button.place(x=10, y=10)
        else:
            tk.Button(header_frame, text="<", command=back_command, bd=0, bg=header_frame.cget("bg"), fg=WHITE, font=("Arial", 14)).place(x=10, y=10)
        
        tk.Label(header_frame, text=title, font=FONT_HEADER, bg=PURPLE_DARK, fg=WHITE).pack(expand=True)

class NotificationPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=GRAY_LIGHT)

        self._create_header("Notifications", lambda: controller.show_frame("MessagePage"))

        tk.Label(self, text="No new notifications.", font=FONT_BODY, bg=GRAY_LIGHT, fg=TEXT_COLOR).pack(pady=50)

    def _create_header(self, title, back_command):
        header_frame = tk.Frame(self, bg=PURPLE_DARK, height=50)
        header_frame.pack(fill="x", pady=(0,0))
        header_frame.pack_propagate(False)

        back_button_img = load_image("arrow.png", (25, 25))
        if back_button_img:
            back_button = tk.Button(header_frame, image=back_button_img, command=back_command, bd=0, bg=header_frame.cget("bg"), cursor="hand2")
            back_button.image = back_button_img
            back_button.place(x=10, y=10)
        else:
            tk.Button(header_frame, text="<", command=back_command, bd=0, bg=header_frame.cget("bg"), fg=WHITE, font=("Arial", 14)).place(x=10, y=10)
        
        tk.Label(header_frame, text=title, font=FONT_HEADER, bg=PURPLE_DARK, fg=WHITE).pack(expand=True)

class HistoryPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=GRAY_LIGHT)

        self._create_header("Booking History", lambda: controller.show_frame("HomePage"))

        # Create a frame to hold the canvas and scrollbar
        scroll_container = tk.Frame(self, bg=GRAY_LIGHT)
        scroll_container.pack(fill="both", expand=True, padx=20, pady=(20, 0))

        # Create Canvas and Scrollbar
        self.canvas = tk.Canvas(scroll_container, bg=WHITE, bd=1, relief="solid", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(scroll_container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack scrollbar to the right
        self.scrollbar.pack(side="right", fill="y")
        # Pack canvas to fill the remaining space
        self.canvas.pack(side="left", fill="both", expand=True)

        # Create a frame inside the canvas to hold the history list
        self.history_list_frame = tk.Frame(self.canvas, bg=WHITE)
        # Store the canvas window ID to modify its width later
        self.history_frame_id = self.canvas.create_window((0, 0), window=self.history_list_frame, anchor="nw")

        # Configure canvas scrolling and responsive width
        self.history_list_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # Add this binding to make the history frame fill the canvas width
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.history_frame_id, width=e.width))
        
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

        # "Clear History" button below the scrollable area
        clear_button = tk.Button(self, text="Clear History", font=FONT_BUTTON,
                                command=self.clear_history,
                                bg="#470366", fg=WHITE,
                                padx=10, pady=5, relief="raised", bd=0, cursor="hand2")
        clear_button.pack(pady=(10, 20))  # Added padding to separate from the list

        self.update_history_display()

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling for the canvas."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def clear_history(self):
        if messagebox.askyesno("Clear All History", "Are you sure you want to delete all booking history?"):
            self.controller.booking_system.clear_all()
            self.update_history_display()
            messagebox.showinfo("Cleared", "All booking history has been cleared.")

    def _create_header(self, title, back_command):
        header_frame = tk.Frame(self, bg=PURPLE_DARK, height=50)
        header_frame.pack(fill="x", pady=(0, 0))
        header_frame.pack_propagate(False)

        back_button_img = load_image("arrow.png", (25, 25))
        if back_button_img:
            back_button = tk.Button(header_frame, image=back_button_img, command=back_command, bd=0, bg=header_frame.cget("bg"), cursor="hand2")
            back_button.image = back_button_img
            back_button.place(x=10, y=10)
        else:
            tk.Button(header_frame, text="<", command=back_command, bd=0, bg=header_frame.cget("bg"), fg=WHITE, font=("Arial", 14)).place(x=10, y=10)
        
        tk.Label(header_frame, text=title, font=FONT_HEADER, bg=PURPLE_DARK, fg=WHITE).pack(expand=True)

    def on_show(self):
        """Called when the frame is shown."""
        self.controller.booking_system.load()  # Ensure bookings are loaded
        self.update_history_display()

    def update_history_display(self):
        # Clear previous history entries
        for widget in self.history_list_frame.winfo_children():
            widget.destroy()

        bookings = self.controller.booking_system.bookings
        if not bookings:    
            tk.Label(self.history_list_frame, text="No past bookings yet.", font=FONT_NORMAL, bg=WHITE, fg=TEXT_COLOR).pack(pady=20)
            return

        for i, booking in enumerate(bookings):
            # Determine action based on status
            action = "CANCELLED" if booking.status == "cancelled" else "BOOKED"
            bg_color = "#eb868f" if booking.status == "cancelled" else "#6ce989"

            booking_frame = tk.Frame(self.history_list_frame, bg=bg_color, bd=1, relief="groove")
            booking_frame.pack(fill="x", padx=5, pady=2)

            tk.Label(booking_frame, text=f"Action: {action}", font=FONT_SUBTITLE, bg=bg_color, fg=TEXT_COLOR, anchor="w").pack(fill="x")
            tk.Label(booking_frame, text=f"Booking ID: {booking.id}", font=FONT_NORMAL, bg=bg_color, fg=TEXT_COLOR, anchor="w").pack(fill="x")
            tk.Label(booking_frame, text=f"Vehicle: {booking.vehicle_type}", font=FONT_NORMAL, bg=bg_color, fg=TEXT_COLOR, anchor="w").pack(fill="x")
            tk.Label(booking_frame, text=f"Route: {booking.start} to {booking.end}", font=FONT_NORMAL, bg=bg_color, fg=TEXT_COLOR, anchor="w").pack(fill="x")
            tk.Label(booking_frame, text=f"Distance: {booking.distance:.1f} km", font=FONT_NORMAL, bg=bg_color, fg=TEXT_COLOR, anchor="w").pack(fill="x")
            tk.Label(booking_frame, text=f"Cost: ₱{booking.cost:.2f} ({booking.payment_method})", font=FONT_NORMAL, bg=bg_color, fg=TEXT_COLOR, anchor="w").pack(fill="x")
            tk.Label(booking_frame, text=f"Status: {booking.status}", font=FONT_NORMAL, bg=bg_color, fg=TEXT_COLOR, anchor="w").pack(fill="x")

            if i < len(bookings) - 1:
                ttk.Separator(self.history_list_frame, orient="horizontal").pack(fill="x", padx=5, pady=5)
                                                           
class PUandDOPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=GRAY_LIGHT)

        self.pickup_location_var = tk.StringVar(self)
        self.dropoff_location_var = tk.StringVar(self)
        self.estimated_distance_var = tk.StringVar(self, value="0.0 km")
        self.estimated_cost_var = tk.StringVar(self, value="₱0.00")

        self.pickup_location_var.trace_add("write", self._update_details)
        self.dropoff_location_var.trace_add("write", self._update_details)

        self._create_header("Pick-up & Drop-off", lambda: controller.show_frame("HomePage"))

        # Main content frame for inputs
        input_frame = tk.Frame(self, bg=WHITE, padx=10, pady=10, relief="solid", bd=1)
        input_frame.pack(pady=20, padx=20, fill="x")

        # Pick-up Location
        tk.Label(input_frame, text="Pick-up Location:", font=FONT_NORMAL, bg=WHITE, fg=TEXT_COLOR).pack(pady=(5, 0), anchor="w")
        self.pickup_menu = ttk.Combobox(input_frame, textvariable=self.pickup_location_var, values=LOCATIONS, state="readonly", font=FONT_NORMAL)
        self.pickup_menu.pack(fill="x", pady=(0, 10))
        self.pickup_menu.set(LOCATIONS[0]) # Default value

        # Drop-off Location
        tk.Label(input_frame, text="Drop-off Location:", font=FONT_NORMAL, bg=WHITE, fg=TEXT_COLOR).pack(pady=(5, 0), anchor="w")
        self.dropoff_menu = ttk.Combobox(input_frame, textvariable=self.dropoff_location_var, values=LOCATIONS, state="readonly", font=FONT_NORMAL)
        self.dropoff_menu.pack(fill="x", pady=(0, 10))
        self.dropoff_menu.set(LOCATIONS[1]) # Default value

        # Estimated Details
        details_frame = tk.Frame(self, bg=WHITE, padx=10, pady=10, relief="solid", bd=1)
        details_frame.pack(pady=10, padx=20, fill="x")

        tk.Label(details_frame, text="Estimated Distance:", font=FONT_SUBTITLE, bg=WHITE, fg=TEXT_COLOR, anchor="w").pack(fill="x")
        tk.Label(details_frame, textvariable=self.estimated_distance_var, font=FONT_NORMAL, bg=WHITE, fg=TEXT_COLOR, anchor="w").pack(fill="x")

        tk.Label(details_frame, text="Estimated Cost:", font=FONT_SUBTITLE, bg=WHITE, fg=TEXT_COLOR, anchor="w").pack(fill="x", pady=(5,0))
        tk.Label(details_frame, textvariable=self.estimated_cost_var, font=FONT_PRICE, bg=WHITE, fg=PURPLE_DARK, anchor="w").pack(fill="x")

        # Confirm Button
        confirm_button = tk.Button(self, text="Confirm Ride", command=self._on_confirm_ride,
                                   font=FONT_BUTTON, bg=PURPLE_DARK, fg=WHITE,
                                   padx=20, pady=10, relief="raised", bd=0, cursor="hand2")
        confirm_button.pack(pady=20)

    def _create_header(self, title, back_command):
        header_frame = tk.Frame(self, bg=PURPLE_DARK, height=50)
        header_frame.pack(fill="x", pady=(0,0))
        header_frame.pack_propagate(False)
        back_button_img = load_image("arrow.png", (25, 25))
        if back_button_img:
            back_button = tk.Button(header_frame, image=back_button_img, command=back_command, bd=0, bg=header_frame.cget("bg"), cursor="hand2")
            back_button.image = back_button_img
            back_button.place(x=10, y=10)
        else:
            tk.Button(header_frame, text="<", command=back_command, bd=0, bg=header_frame.cget("bg"), fg=WHITE, font=("Arial", 14)).place(x=10, y=10)
        tk.Label(header_frame, text=title, font=FONT_HEADER, bg=PURPLE_DARK, fg=WHITE).pack(expand=True)

    def _update_details(self, *args):
        pickup = self.pickup_location_var.get()
        dropoff = self.dropoff_location_var.get()
        vehicle_type = self.controller.current_booking_details.get("vehicle_type", "Enavroom-vroom")  # Default to Moto Taxi if not set

        if pickup and dropoff and pickup != dropoff:
            distance = get_distance(pickup, dropoff)
            cost = self.controller.booking_system.calculate_cost(vehicle_type, distance)
            self.estimated_distance_var.set(f"{distance:.1f} km")
            self.estimated_cost_var.set(f"₱{cost:.2f}")
        else:
            self.estimated_distance_var.set("0.0 km")
            self.estimated_cost_var.set("₱0.00")

    def _on_confirm_ride(self):
        pickup = self.pickup_location_var.get()
        dropoff = self.dropoff_location_var.get()

        if not pickup or not dropoff:
            messagebox.showerror("Error", "Please select both pick-up and drop-off locations.")
            return
        if pickup == dropoff:
            messagebox.showerror("Error", "Pick-up and drop-off locations cannot be the same.")
            return
        
        distance = get_distance(pickup, dropoff)
        if distance == 0.0:
            messagebox.showerror("Error", f"No route defined between {pickup} and {dropoff}. Please select different locations.")
            return

        vehicle_type = self.controller.current_booking_details.get("vehicle_type", "Enavroom-vroom")
        cost = self.controller.booking_system.calculate_cost(vehicle_type, distance)
        self.controller.update_booking_details(
            pickup_location=pickup,
            dropoff_location=dropoff,
            distance=distance,
            cost=cost
        )
        self.controller.show_frame("MapPage")

    def on_show(self):
        self._update_details()  # Recalculate cost/distance when page is shown

class MapPage(tk.Frame):
    # Define constants at class level
    CENTER_PADX_VEHICLE = 60
    CENTER_PADX_PAYMENT_BOOK = 30

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=GRAY_LIGHT)

        self.current_selected_vehicle_frame = None
        self.selected_vehicle_type = tk.StringVar(value="")
        self.selected_payment_method = tk.StringVar(value="Cash")

        # Retrieve booking details from controller
        self.pickup_location_display = self.controller.current_booking_details.get("pickup_location", "PUP Main")
        self.dropoff_location_display = self.controller.current_booking_details.get("dropoff_location", "PUP LHS")
        self.trip_distance = self.controller.current_booking_details.get("distance", get_distance(self.pickup_location_display, self.dropoff_location_display))
        self.initial_vehicle_type = self.controller.current_booking_details.get("vehicle_type", "Enavroom-vroom")

        self._create_header(f"{self.pickup_location_display} → {self.dropoff_location_display}", lambda: controller.show_frame("PUandDOPage"))

        # --- Top Map Section ---
        map_header_frame = tk.Frame(self, bg=PURPLE_DARK, height=50)
        map_header_frame.pack(fill="x", pady=(0, 0))

# --- Dynamic Map Image Logic ---
        map_filename = ROUTE_IMAGE_MAP.get((self.pickup_location_display, self.dropoff_location_display))
        if not map_filename:
            map_filename = ROUTE_IMAGE_MAP.get((self.dropoff_location_display, self.pickup_location_display))
        
        if map_filename:
            map_img = load_image(map_filename, (375, 160))
            if map_img:
                map_label = tk.Label(self, image=map_img, bg=GRAY_LIGHT)
                map_label.image = map_img
                map_label.pack(fill="x", pady=(0, 0))
            else:
                map_placeholder_label = tk.Label(self, text=f"Map Not Found\n(Tried: {map_filename})",
                                                font=("Arial", 12), bg="lightgray", fg="darkgray", height=8, wraplength=250)
                map_placeholder_label.pack(fill="x", expand=False, pady=(0, 0))
        else:
            map_placeholder_label = tk.Label(self, text=f"Map Not Found\n(Route: {self.pickup_location_display} to {self.dropoff_location_display})",
                                            font=("Arial", 12), bg="lightgray", fg="darkgray", height=8, wraplength=250)
            map_placeholder_label.pack(fill="x", expand=False, pady=(0, 0))
            
        self.scrollable_frame = tk.Frame(self, bg=GRAY_LIGHT)
        self.scrollable_frame.pack(fill="both", expand=True)

        tk.Label(self.scrollable_frame, text="Choose your Enavroom", font=FONT_TITLE, bg=GRAY_LIGHT, fg=TEXT_COLOR).pack(pady=(10, 10))

        self.vehicle_option_frames = []

        # Define vehicle options based on initial vehicle type from HomePage
        vehicle_configs = []
        if self.initial_vehicle_type == "Enavroom-vroom":
            vehicle_configs = [ 
                {"type": "Enavroom-vroom", "icon": "enavroom.png", "title": "Enavroom-vroom", "passengers": "1", "description": "Beat the traffic on a motorcycle ride."}
            ]
        elif "Car" in self.initial_vehicle_type:
            vehicle_configs = [
                {"type": "Car (4-seater)", "icon": "enacar.png", "title": "Car (4-seater)", "passengers": "4", "description": "Get around town affordably, up to 4 passengers."},
                {"type": "Car (6-seater)", "icon": "enacar.png", "title": "Car (6-seater)", "passengers": "6", "description": "Roomy and affordable rides for up to six."}
            ]

        for config in vehicle_configs:
            calculated_price = self.controller.booking_system.calculate_cost(config["type"], self.trip_distance)
            option_data = {
                "icon": config["icon"],
                "title": config["title"],
                "passengers": config["passengers"],
                "description": config["description"],
                "price": f"{calculated_price:.2f}"
            }
            frame = self.create_service_option(self.scrollable_frame, **option_data)
            frame.pack(fill="x", padx=self.CENTER_PADX_VEHICLE, pady=5)
            self.vehicle_option_frames.append((frame, config["type"]))
            bind_widgets_recursively(frame, lambda e, f=frame, t=config["type"]: self.select_vehicle_option(f, t))

        # Pre-select the vehicle type from HomePage
        for frame, vehicle_type_name in self.vehicle_option_frames:
            if vehicle_type_name == self.initial_vehicle_type:
                self.select_vehicle_option(frame, vehicle_type_name)
                break

        payment_frame = tk.Frame(self.scrollable_frame, bg=WHITE, bd=1, relief="solid", padx=10, pady=5)
        payment_frame.pack(fill="x", padx=self.CENTER_PADX_PAYMENT_BOOK, pady=(10, 10))

        cash_img = load_image("cash_2.png", (30, 30))
        cash_button_frame = tk.Frame(payment_frame, bg=WHITE)
        cash_button_frame.pack(side="left", expand=True, padx=10)
        if cash_img:
            cash_icon_label = tk.Label(cash_button_frame, image=cash_img, bg=WHITE)
            cash_icon_label.image = cash_img
            cash_icon_label.pack(pady=(5, 0))
        else:
            tk.Label(cash_button_frame, text="C", font=("Arial", 20), bg="lightgray", relief="solid").pack(pady=(0, 5))
        tk.Label(cash_button_frame, text="Cash", font=FONT_SUBTITLE, bg=WHITE, fg=TEXT_COLOR).pack()
        bind_widgets_recursively(cash_button_frame, lambda e: self.select_payment_method("Cash"))

        wallet_img = load_image("wallet_2.png", (30, 30))
        wallet_button_frame = tk.Frame(payment_frame, bg=WHITE)
        wallet_button_frame.pack(side="left", expand=True, padx=10)
        if wallet_img:
            wallet_icon_label = tk.Label(wallet_button_frame, image=wallet_img, bg=WHITE)
            wallet_icon_label.image = wallet_img
            wallet_icon_label.pack(pady=(5, 0))
        else:
            tk.Label(wallet_button_frame, text="W", font=("Arial", 20), bg="lightgray", relief="solid").pack(pady=(0, 5))
        tk.Label(wallet_button_frame, text="Wallet", font=FONT_SUBTITLE, bg=WHITE, fg=TEXT_COLOR).pack()
        bind_widgets_recursively(wallet_button_frame, lambda e: self.select_payment_method("Wallet"))

        book_now_button = tk.Button(self.scrollable_frame, text="Book Now", command=self.on_book_now,
                                    font=FONT_BUTTON, bg=PURPLE_DARK, fg=WHITE,
                                    padx=20, pady=10, relief="raised", bd=0, cursor="hand2")
        book_now_button.pack(fill="x", padx=self.CENTER_PADX_PAYMENT_BOOK, pady=(10, 10))

    def _create_header(self, title, back_command):
        header_frame = tk.Frame(self, bg=PURPLE_DARK, height=50)
        header_frame.pack(fill="x", pady=(0, 0))
        header_frame.pack_propagate(False)
        back_button_img = load_image("arrow.png", (25, 25))
        if back_button_img:
            back_button = tk.Button(header_frame, image=back_button_img, command=back_command, bd=0, bg=header_frame.cget("bg"), cursor="hand2")
            back_button.image = back_button_img
            back_button.place(x=10, y=10)
        else:
            tk.Button(header_frame, text="<", command=back_command, bd=0, bg=header_frame.cget("bg"), fg=WHITE, font=("Arial", 14)).place(x=10, y=10)
        tk.Label(header_frame, text=title, font=FONT_HEADER, bg=PURPLE_DARK, fg=WHITE).pack(expand=True)

    def create_service_option(self, parent, icon, title, passengers, description, price):
        frame = tk.Frame(parent, bg=WHITE, bd=1, relief="solid",
                         highlightbackground="light grey", highlightthickness=1,
                         padx=8, pady=6)

        icon_size = (30, 30)
        icon_image = load_image(icon, icon_size)
        if icon_image:
            icon_label = tk.Label(frame, image=icon_image, bg=WHITE)
            icon_label.image = icon_image
            icon_label.grid(row=0, column=0, rowspan=2, padx=(0, 8), pady=2, sticky="ns")
        else:
            fallback_text = title[0] if title else "?"
            fallback_label = tk.Label(frame, text=fallback_text, font=("Arial", 16, "bold"), bg=WHITE, fg=PURPLE_DARK, width=3, height=2, bd=1, relief="solid")
            fallback_label.grid(row=0, column=0, rowspan=2, padx=(0, 8), pady=2, sticky="ns")

        text_frame = tk.Frame(frame, bg=WHITE)
        text_frame.grid(row=0, column=1, rowspan=2, sticky="nw")

        tk.Label(text_frame, text=f"{title}", font=FONT_SUBTITLE, bg=WHITE, fg=TEXT_COLOR, anchor="w").pack(fill="x", expand=True)
        tk.Label(text_frame, text=f"• {passengers} passengers", font=FONT_NORMAL, bg=WHITE, fg="gray", anchor="w").pack(fill="x", expand=True)
        tk.Label(text_frame, text=description, font=FONT_NORMAL, bg=WHITE, fg="gray", anchor="w", wraplength=170, justify="left").pack(fill="x", expand=True)

        tk.Label(frame, text=f"₱{price}", font=FONT_PRICE, bg=WHITE, fg=PURPLE_DARK).grid(row=0, column=2, padx=(8, 0), sticky="ne")

        frame.grid_columnconfigure(1, weight=1)
        return frame

    def select_vehicle_option(self, selected_frame, vehicle_type_name):
        if self.current_selected_vehicle_frame and self.current_selected_vehicle_frame.winfo_exists():
            self.current_selected_vehicle_frame.config(highlightbackground="light grey", highlightthickness=1)
        selected_frame.config(highlightbackground=HIGHLIGHT_COLOR, highlightthickness=2)
        self.current_selected_vehicle_frame = selected_frame
        self.selected_vehicle_type.set(vehicle_type_name)
        print(f"Selected vehicle: {vehicle_type_name}")

    def select_payment_method(self, method):
        self.selected_payment_method.set(method)
        print(f"Selected payment method: {method}")

    def on_book_now(self):
        selected_vehicle_type = self.selected_vehicle_type.get()
        selected_payment = self.selected_payment_method.get()

        if not selected_vehicle_type:
            messagebox.showwarning("Selection Missing", "Please select a vehicle type before booking.")
            return

        final_cost = self.controller.booking_system.calculate_cost(selected_vehicle_type, self.trip_distance)
        booking = self.controller.booking_system.book(
            selected_vehicle_type,
            self.pickup_location_display,
            self.dropoff_location_display,
            selected_payment
        )
        if booking:
            self.controller.update_booking_details(
                vehicle_type=selected_vehicle_type,
                cost=final_cost,
                payment_method=selected_payment,
                booking_id=booking.id
            )
            self.controller.show_frame("LoadingPage")
        else:
            messagebox.showerror("Error", "Failed to confirm booking.")

    def on_show(self):
        # Update booking details when shown
        pickup = self.controller.current_booking_details.get("pickup_location", "PUP Main")
        dropoff = self.controller.current_booking_details.get("dropoff_location", "PUP LHS")
        vehicle_type = self.controller.current_booking_details.get("vehicle_type", "Enavroom-vroom")
        self.pickup_location_display = pickup
        self.dropoff_location_display = dropoff
        self.trip_distance = self.controller.current_booking_details.get("distance", get_distance(pickup, dropoff))
        self.initial_vehicle_type = vehicle_type

        # Recreate the header and map section
        for widget in self.winfo_children():
            widget.destroy()
        self.current_selected_vehicle_frame = None
        self._create_header(f"{self.pickup_location_display} → {self.dropoff_location_display}", lambda: self.controller.show_frame("PUandDOPage"))

        map_filename = ROUTE_IMAGE_MAP.get((self.pickup_location_display, self.dropoff_location_display))
        if not map_filename:
            map_filename = ROUTE_IMAGE_MAP.get((self.dropoff_location_display, self.pickup_location_display))
            print(f"DEBUG: Checking reverse route: {self.dropoff_location_display} -> {self.pickup_location_display}")

        if map_filename:
            print(f"DEBUG: Map filename found: {map_filename}")
            map_img = load_image(map_filename, (375, 160))
            if map_img:
                print(f"DEBUG: Successfully loaded map image: {map_filename}")
                map_label = tk.Label(self, image=map_img, bg=GRAY_LIGHT)
                map_label.image = map_img
                map_label.pack(fill="x", pady=(0, 0))
            else:
                print(f"DEBUG: Failed to load map image: {map_filename}")
                map_placeholder_label = tk.Label(self, text=f"Map Not Found\n(Tried: {map_filename})",
                                                font=("Arial", 12), bg="lightgray", fg="darkgray", height=8, wraplength=250)
                map_placeholder_label.pack(fill="x", expand=False, pady=(0, 0))
        else:
            print(f"DEBUG: No map filename found for route: {self.pickup_location_display} to {self.dropoff_location_display}")
            map_placeholder_label = tk.Label(self, text=f"Map Not Found\n(Route: {self.pickup_location_display} to {self.dropoff_location_display})",
                                            font=("Arial", 12), bg="lightgray", fg="darkgray", height=8, wraplength=250)
            map_placeholder_label.pack(fill="x", expand=False, pady=(0, 0))


        self.scrollable_frame = tk.Frame(self, bg=GRAY_LIGHT)
        self.scrollable_frame.pack(fill="both", expand=True)
        tk.Label(self.scrollable_frame, text="Choose your Enavroom", font=FONT_TITLE, bg=GRAY_LIGHT, fg=TEXT_COLOR).pack(pady=(10, 10))

        self.vehicle_option_frames = []
        # Define vehicle options based on initial vehicle type from HomePage
        vehicle_configs = []
        if self.initial_vehicle_type == "Enavroom-vroom":
            vehicle_configs = [
                {"type": "Enavroom-vroom", "icon": "enavroom.png", "title": "Enavroom-vroom", "passengers": "1", "description": "Beat the traffic on a motorcycle ride."}
            ]
        elif "Car" in self.initial_vehicle_type:
            vehicle_configs = [
                {"type": "Car (4-seater)", "icon": "car.png", "title": "Car (4-seater)", "passengers": "4", "description": "Get around town affordably, up to 4 passengers."},
                {"type": "Car (6-seater)", "icon": "car.png", "title": "Car (6-seater)", "passengers": "6", "description": "Roomy and affordable rides for up to six."}
            ]

        for config in vehicle_configs:
            calculated_price = self.controller.booking_system.calculate_cost(config["type"], self.trip_distance)
            option_data = {
                "icon": config["icon"],
                "title": config["title"],
                "passengers": config["passengers"],
                "description": config["description"],
                "price": f"{calculated_price:.2f}"
            }
            frame = self.create_service_option(self.scrollable_frame, **option_data)
            frame.pack(fill="x", padx=self.CENTER_PADX_VEHICLE, pady=5)
            self.vehicle_option_frames.append((frame, config["type"]))
            bind_widgets_recursively(frame, lambda e, f=frame, t=config["type"]: self.select_vehicle_option(f, t))

        for frame, vehicle_type_name in self.vehicle_option_frames:
            if vehicle_type_name == self.initial_vehicle_type:
                self.select_vehicle_option(frame, vehicle_type_name)
                break

        payment_frame = tk.Frame(self.scrollable_frame, bg=WHITE, bd=1, relief="solid", padx=10, pady=5)
        payment_frame.pack(fill="x", padx=self.CENTER_PADX_PAYMENT_BOOK, pady=(10, 10))

        cash_img = load_image("cash_2.png", (30, 30))
        cash_button_frame = tk.Frame(payment_frame, bg=WHITE)
        cash_button_frame.pack(side="left", expand=True, padx=10)
        if cash_img:
            cash_icon_label = tk.Label(cash_button_frame, image=cash_img, bg=WHITE)
            cash_icon_label.image = cash_img
            cash_icon_label.pack(pady=(5, 0))
        else:
            tk.Label(cash_button_frame, text="C", font=("Arial", 20), bg="lightgray", relief="solid").pack(pady=(0, 5))
        tk.Label(cash_button_frame, text="Cash", font=FONT_SUBTITLE, bg=WHITE, fg=TEXT_COLOR).pack()
        bind_widgets_recursively(cash_button_frame, lambda e: self.select_payment_method("Cash"))

        wallet_img = load_image("wallet_2.png", (30, 30))
        wallet_button_frame = tk.Frame(payment_frame, bg=WHITE)
        wallet_button_frame.pack(side="left", expand=True, padx=10)
        if wallet_img:
            wallet_icon_label = tk.Label(wallet_button_frame, image=wallet_img, bg=WHITE)
            wallet_icon_label.image = wallet_img
            wallet_icon_label.pack(pady=(5, 0))
        else:
            tk.Label(wallet_button_frame, text="W", font=("Arial", 20), bg="lightgray", relief="solid").pack(pady=(0, 5))
        tk.Label(wallet_button_frame, text="Wallet", font=FONT_SUBTITLE, bg=WHITE, fg=TEXT_COLOR).pack()
        bind_widgets_recursively(wallet_button_frame, lambda e: self.select_payment_method("Wallet"))

        book_now_button = tk.Button(self.scrollable_frame, text="Book Now", command=self.on_book_now,
                                    font=FONT_BUTTON, bg=PURPLE_DARK, fg=WHITE,
                                    padx=20, pady=10, relief="raised", bd=0, cursor="hand2")
        book_now_button.pack(fill="x", padx=self.CENTER_PADX_PAYMENT_BOOK, pady=(10, 10))  

class LoadingPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=GRAY_LIGHT)

        self.loading_label = tk.Label(self, text="Finding a driver...", font=("Arial", 20, "bold"), bg=GRAY_LIGHT, fg=TEXT_COLOR)
        self.loading_label.pack(pady=100)

        # Simple animation for loading dots
        self.dots_count = 0
        self.after_id = None # To store the after method ID for cancellation

        cancel_button = tk.Button(self, text="Cancel Booking", command=self._on_cancel_booking,
                                   font=FONT_BUTTON, bg=RED_COLOR, fg=WHITE,
                                   padx=20, pady=10, relief="raised", bd=0, cursor="hand2")
        cancel_button.pack(pady=30)

    def on_show(self):
        self.dots_count = 0
        self._animate_loading()
        # Schedule the transition after a delay (e.g., 3 seconds)
        # Cancel any previous pending transition
        if hasattr(self, 'transition_id') and self.transition_id:
            self.after_cancel(self.transition_id)
        self.transition_id = self.after(3000, self._transition_to_driver_found) # 3 seconds delay

    def on_hide(self):
        # Stop animation when leaving the page
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        if hasattr(self, 'transition_id') and self.transition_id:
            self.after_cancel(self.transition_id)
            self.transition_id = None

    def _animate_loading(self):
        self.dots_count = (self.dots_count + 1) % 4
        dots = "." * self.dots_count
        self.loading_label.config(text=f"Finding a driver{dots}")
        self.after_id = self.after(500, self._animate_loading) # Update every 500ms

    def _transition_to_driver_found(self):
        self.on_hide() # Stop animation and pending transitions
        vehicle_type = self.controller.current_booking_details.get("vehicle_type")
        if "Car" in vehicle_type:
            self.controller.show_frame("WeFoundDriverEnacarPage")
        else: # Default to Enavroom-vroom
            self.controller.show_frame("WeFoundDriverEnavroomPage")

    def _on_cancel_booking(self):
        # cancel booking -> home_page.py
        booking_id = self.controller.current_booking_details.get("booking_id")
        if booking_id and self.controller.booking_system.cancel(booking_id):
            messagebox.showinfo("Cancelled", "Your booking has been cancelled.")
        else:
            messagebox.showwarning("Error", "Could not cancel booking or no active booking found.")
        self.controller.show_frame("HomePage")
        self.on_hide() # Stop any ongoing animations/timers

class WeFoundDriverBasePage(tk.Frame):
    """Base class for 'We Found Your Driver' pages."""
    def __init__(self, parent, controller, vehicle_type_display, driver_icon):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=GRAY_LIGHT)

        self.vehicle_type_display = vehicle_type_display
        self.driver_icon = driver_icon

        self._create_header("Driver Found!", lambda: self._on_cancel_ride()) # "Cancel Ride"

        tk.Label(self, text=f"We found your driver for your {self.vehicle_type_display}!", font=FONT_TITLE, bg=GRAY_LIGHT, fg=TEXT_COLOR, wraplength=300).pack(pady=20)

        # Driver icon
        driver_img = load_image(self.driver_icon, (100, 100), is_circular=True)
        if driver_img:
            driver_label = tk.Label(self, image=driver_img, bg=GRAY_LIGHT)
            driver_label.image = driver_img
            driver_label.pack(pady=10)
        else:
            tk.Label(self, text="Driver Pic", font=("Arial", 16), bg="lightgray", width=10, height=5).pack(pady=10)

        tk.Label(self, text="Driver Name: John Doe", font=FONT_BODY, bg=GRAY_LIGHT, fg=TEXT_COLOR).pack(pady=5)
        tk.Label(self, text="Plate No: ABC 123", font=FONT_BODY, bg=GRAY_LIGHT, fg=TEXT_COLOR).pack(pady=5)
        tk.Label(self, text="ETA: 5 mins", font=FONT_BODY, bg=GRAY_LIGHT, fg=TEXT_COLOR).pack(pady=5)

        self.cancel_button = tk.Button(self, text="Cancel Ride", command=self._on_cancel_ride,
                                         font=FONT_BUTTON, bg=RED_COLOR, fg=WHITE,
                                         padx=20, pady=10, relief="raised", bd=0, cursor="hand2")
        self.cancel_button.pack(pady=(20, 10))

        self.after_id_transition = None # To hold transition to DonePage

    def _create_header(self, title, back_command):
        header_frame = tk.Frame(self, bg=PURPLE_DARK, height=50)
        header_frame.pack(fill="x", pady=(0,0))
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text=title, font=FONT_HEADER, bg=PURPLE_DARK, fg=WHITE).pack(expand=True)
        
        # Adding a simple 'x' button for consistency in cancelling at this stage
        cancel_btn = tk.Button(header_frame, text="X", command=back_command, bd=0, bg=header_frame.cget("bg"), fg=WHITE, font=("Arial", 14), cursor="hand2")
        cancel_btn.place(relx=0.9, rely=0.5, anchor="center") # Top right corner

    def on_show(self):
        # Automatically transition to DonePage after a delay
        if self.after_id_transition:
            self.after_cancel(self.after_id_transition)
        self.after_id_transition = self.after(5000, self._transition_to_done) # 5 seconds delay to done page

    def on_hide(self):
        if self.after_id_transition:
            self.after_cancel(self.after_id_transition)
            self.after_id_transition = None

    def _on_cancel_ride(self):
        # If cancel button clicked -> HomePage
        booking_id = self.controller.current_booking_details.get("booking_id")
        if booking_id and self.controller.booking_system.cancel(booking_id):
            messagebox.showinfo("Ride Cancelled", "Your ride has been cancelled.")
        else:
            messagebox.showwarning("Error", "Could not cancel ride or no active booking found.")
        self.controller.show_frame("HomePage")
        self.on_hide()

    def _transition_to_done(self):
        self.on_hide()
        self.controller.show_frame("DonePage")


class WeFoundDriverEnacarPage(WeFoundDriverBasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Car", "driver_car.png") # Driver icon specific to car

class WeFoundDriverEnavroomPage(WeFoundDriverBasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Enavroom-vroom", "driver_moto.png") # Driver icon specific to moto


class DonePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=GRAY_LIGHT)

        self._create_header("Ride Completed!", lambda: self.controller.show_frame("HomePage")) # Back to home
        tk.Label(self, text="Your ride is complete!", font=("Arial", 20, "bold"), bg=GRAY_LIGHT, fg=GREEN_COLOR).pack(pady=50)
        thanks_img = load_image("thanks.png", size=(339, 225))
        if thanks_img:
            thanks_label = tk.Label(self, image=thanks_img, bg=GRAY_LIGHT)
            thanks_label.image = thanks_img  # Keep a reference to prevent garbage collection
            thanks_label.pack(pady=20)


        
        
        # Summary of the booking
        self.summary_label = tk.Label(self, text="", font=FONT_BODY, bg=GRAY_LIGHT, fg=TEXT_COLOR, wraplength=300, justify="center")
        self.summary_label.pack(pady=20)

        done_button = tk.Button(self, text="Done", command=lambda: controller.show_frame("HomePage"),
                                font=FONT_BUTTON, bg=PURPLE_DARK, fg=WHITE,
                                padx=20, pady=10, relief="raised", bd=0, cursor="hand2")
        done_button.pack(pady=(20, 10))

        exit_button = tk.Button(self, text="Exit Application", command=controller.exit_app,
                                font=FONT_BUTTON, bg=RED_COLOR, fg=WHITE,
                                padx=20, pady=10, relief="raised", bd=0, cursor="hand2")
        exit_button.pack(pady=5)

    def _create_header(self, title, back_command):
        header_frame = tk.Frame(self, bg=PURPLE_DARK, height=50)
        header_frame.pack(fill="x", pady=(0,0))
        header_frame.pack_propagate(False)
        tk.Label(header_frame, text=title, font=FONT_HEADER, bg=PURPLE_DARK, fg=WHITE).pack(expand=True)

    def on_show(self):
        # Display final booking details
        details = self.controller.current_booking_details
        booking_id = details.get("booking_id")

    def clear_history(self):
        if messagebox.askyesno("Clear All History", "Are you sure you want to delete all booking history?"):
            self.controller.booking_system.clear_all()
            # Also clear the .txt log
            open("booking_log.txt", "w").close()
            self.update_history_display()
            messagebox.showinfo("Cleared", "All booking history has been cleared.")

        # summary_text = (
        #     f"Vehicle: {details.get('vehicle_type', 'N/A')}\n"
        #     f"From: {details.get('pickup_location', 'N/A')}\n"
        #     f"To: {details.get('dropoff_location', 'N/A')}\n"
        #     f"Distance: {details.get('distance', 0):.1f} km\n"
        #     f"Total Paid: ₱{details.get('cost', 0):.2f} ({details.get('payment_method', 'N/A')})"
        # )
        # self.summary_label.config(text=summary_text)
        # # Clear current booking details after showing the done page
        # self.controller.current_booking_details = {
        #     "vehicle_type": "", "pickup_location": "", "dropoff_location": "",
        #     "distance": 0, "cost": 0, "payment_method": "Cash", "booking_id": None
        # }

# --- Main execution block ---
if __name__ == "__main__":
    # Get all unique map file names from the imported dictionary
    map_files_to_create = set(ROUTE_IMAGE_MAP.values())

    # Define dummy image files and their sizes for automatic creation
    dummy_images = {
        "logo_enavroom.png": (250, 80),
        "moto_taxi.png": (60, 60),
        "car.png": (60, 60),
        "home.png": (30, 30),
        "message.png": (30, 30),
        "history.png": (30, 30),
        "arrow.png": (25, 25),
        "enavroom.png": (30, 30),
        "enacar.png": (50, 50),
        "cash_2.png": (30, 30),
        "wallet_2.png": (30, 30),
        "driver_moto.png": (100, 100),
        "driver_car.png": (100, 100),
        "driver_waving.png": (150, 150)
    }

    # Add all map files from ROUTE_IMAGE_MAP to the dummy image creation list
    for map_file in map_files_to_create:
        if map_file: # Ensure the filename is not empty
            dummy_images[map_file] = (375, 160)

    # Ensure the IMAGE_BASE_PATH exists
    # ... (the rest of your file from this point is correct and does not need to be changed) ...

    # Ensure the IMAGE_BASE_PATH exists
    if not os.path.exists(IMAGE_BASE_PATH):
        os.makedirs(IMAGE_BASE_PATH)
        print(f"Created directory: {IMAGE_BASE_PATH}")

    # Create dummy image files if they don't exist
    for img_name, img_size in dummy_images.items():
        filepath = os.path.join(IMAGE_BASE_PATH, img_name)
        if not os.path.exists(filepath):
            try:
                # Specific dummy image generation for better visual representation
                if "enavroom_logo.png" in img_name:
                    dummy_img = Image.new('RGB', img_size, color='purple')
                    d = ImageDraw.Draw(dummy_img)
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.5))
                    except IOError:
                        font = ImageFont.load_default()
                    d.text((5, 5), "ENAVROOM", fill=(255,255,255), font=font)
                elif "moto_taxi.png" in img_name: # Circular
                    dummy_img = Image.new('RGB', img_size, color='orange')
                    d = ImageDraw.Draw(dummy_img)
                    d.ellipse((0, 0) + img_size, fill=(255, 165, 0)) # Orange circle background
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.4))
                    except IOError:
                        font = ImageFont.load_default()
                    d.text((img_size[0]*0.2, img_size[1]*0.3), "Bike", fill=(0,0,0), font=font)
                elif "car.png" in img_name: # Circular
                    dummy_img = Image.new('RGB', img_size, color='blue')
                    d = ImageDraw.Draw(dummy_img)
                    d.ellipse((0, 0) + img_size, fill=(0, 0, 255)) # Blue circle background
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.4))
                    except IOError:
                        font = ImageFont.load_default()
                    d.text((img_size[0]*0.25, img_size[1]*0.3), "Car", fill=(255,255,255), font=font)
                elif "enavroom.png" in img_name: # Rectangle
                    dummy_img = Image.new('RGB', img_size, color='purple')
                    d = ImageDraw.Draw(dummy_img)
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.5))
                    except IOError:
                        font = ImageFont.load_default()
                    d.text((5, 5), "E-V", fill=(255,255,255), font=font)
                elif "enacar_2.png" in img_name: # Rectangle
                    dummy_img = Image.new('RGB', img_size, color='darkgreen')
                    d = ImageDraw.Draw(dummy_img)
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.5))
                    except IOError:
                        font = ImageFont.load_default()
                    d.text((5, 5), "Car", fill=(255,255,255), font=font)
                elif "cash_2.png" in img_name:
                    dummy_img = Image.new('RGB', img_size, color='green')
                    d = ImageDraw.Draw(dummy_img)
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.5))
                    except IOError:
                        font = ImageFont.load_default()
                    d.text((5, 5), "Cash", fill=(255,255,255), font=font)
                elif "wallet_2.png" in img_name:
                    dummy_img = Image.new('RGB', img_size, color='blue')
                    d = ImageDraw.Draw(dummy_img)
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.5))
                    except IOError:
                        font = ImageFont.load_default()
                    d.text((5, 5), "Wal", fill=(255,255,255), font=font)
                elif "arrow.png" in img_name:
                    dummy_img = Image.new('RGB', img_size, color = 'darkgray')
                    d = ImageDraw.Draw(dummy_img)
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.7))
                    except IOError:
                        font = ImageFont.load_default()
                    d.text((int(img_size[0]*0.2), -2), "<", fill=(0,0,0), font=font)
                elif "driver_moto.png" in img_name: # Circular
                    dummy_img = Image.new('RGB', img_size, color = 'red')
                    d = ImageDraw.Draw(dummy_img)
                    d.ellipse((0, 0) + img_size, fill=(255, 0, 0)) # Red circle
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.3))
                    except IOError:
                        font = ImageFont.load_default()
                    d.text((img_size[0]*0.1, img_size[1]*0.35), "Driver", fill=(255,255,255), font=font)
                elif "driver_car.png" in img_name: # Circular
                    dummy_img = Image.new('RGB', img_size, color = 'darkblue')
                    d = ImageDraw.Draw(dummy_img)
                    d.ellipse((0, 0) + img_size, fill=(0, 0, 139)) # Dark blue circle
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.3))
                    except IOError:
                        font = ImageFont.load_default()
                    d.text((img_size[0]*0.15, img_size[1]*0.35), "Driver", fill=(255,255,255), font=font)
                elif "_icon.png" in img_name or ".png" in img_name: # Generic icon placeholder for nav bar, etc.
                    dummy_img = Image.new('RGB', img_size, color='lightgray')
                    d = ImageDraw.Draw(dummy_img)
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.5))
                    except IOError:
                        font = ImageFont.load_default()
                    text_to_draw = img_name.split('.')[0][0].upper()
                    if "message" in img_name: text_to_draw = "Msg"
                    d.text((5,5), text_to_draw, fill=(0,0,0), font=font)
                else: # Default for other images, e.g., maps
                    dummy_img = Image.new('RGB', img_size, color = 'lightgray')
                    d = ImageDraw.Draw(dummy_img)
                    try:
                        font = ImageFont.truetype("arial.ttf", int(img_size[1] * 0.15))
                    except IOError:
                        font = ImageFont.load_default()
                    text_on_map = img_name.replace(".png", "").replace("_", " ").title()
                    bbox = d.textbbox((0, 0), text_on_map, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    x = (img_size[0] - text_width) / 2
                    y = (img_size[1] - text_height) / 2
                    d.text((x, y), text_on_map, fill=(0,0,0), font=font)
                
                dummy_img.save(filepath)
                print(f"Created dummy image: {filepath}")
            except Exception as e:
                print(f"Could not create dummy image {filepath}: {e}")

    app = App()
    app.mainloop()

