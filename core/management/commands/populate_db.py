import os
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import OrganizerProfile, User
from checkin.models import CheckIn
from events.models import Event, EventCategory, EventImage, Venue
from orders.models import Attendee, Order, OrderItem
from promotions.models import PromoCode
from tickets.models import Ticket, TicketType


def attach_seed_image(event, filename, is_primary=True):
    """Attaches a pre-generated seed image to the event."""
    seed_path = os.path.join(settings.BASE_DIR, "media", "seed_images", filename)
    if os.path.exists(seed_path):
        with open(seed_path, "rb") as f:
            EventImage.objects.create(
                event=event,
                image=File(f, name=filename),
                is_primary=is_primary
            )
    else:
        print(f"Warning: Seed image {filename} not found at {seed_path}")


class Command(BaseCommand):
    help = "Resets the database and populates it with mock data"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Deleting all data..."))

        # Delete strictly in order of dependencies to avoid ProtectedError/IntegrityError
        CheckIn.objects.all().delete()
        Attendee.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        PromoCode.objects.all().delete()
        Ticket.objects.all().delete()
        TicketType.objects.all().delete()
        EventImage.objects.all().delete()
        Event.objects.all().delete()
        Venue.objects.all().delete()
        EventCategory.objects.all().delete()
        OrganizerProfile.objects.all().delete()
        User.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("Data deleted successfully."))

        # Create Users
        self.stdout.write("Creating users...")

        # Organizers
        org1 = User.objects.create(
            username="org1",
            email="org1@gmail.com",
            password=make_password("asdfasdf"),
            is_organizer=True,
        )
        OrganizerProfile.objects.create(
            user=org1,
            organization_name="Stellar Events",
            contact_email="contact@stellarevents.com",
            contact_phone="1234567890",
            verified=True,
        )

        org2 = User.objects.create(
            username="org2",
            email="org2@gmail.com",
            password=make_password("asdfasdf"),
            is_organizer=True,
        )
        OrganizerProfile.objects.create(
            user=org2,
            organization_name="Neon Nights",
            contact_email="info@neonnights.com",
            contact_phone="0987654321",
            verified=True,
        )

        # Normal Users
        user1 = User.objects.create(username="user1", email="user1@gmail.com", password=make_password("asdfasdf"))
        user2 = User.objects.create(username="user2", email="user2@gmail.com", password=make_password("asdfasdf"))

        # Create Venues
        self.stdout.write("Creating venues...")
        venue1 = Venue.objects.create(
            name="Grand Hall", address="123 Main St", city="New York", capacity=500
        )
        venue2 = Venue.objects.create(
            name="Open Air Arena",
            address="456 Park Ave",
            city="Los Angeles",
            capacity=2000,
        )

        # Create Categories
        self.stdout.write("Creating categories...")
        cat_music = EventCategory.objects.create(name="Music", slug="music")
        cat_tech = EventCategory.objects.create(name="Technology", slug="technology")
        cat_art = EventCategory.objects.create(name="Art", slug="art")

        # Create Events
        self.stdout.write("Creating events...")
        now = timezone.now()

        event1 = Event.objects.create(
            organizer=org1.organizer_profile,
            category=cat_music,
            venue=venue1,
            title="Summer Vibes Concert",
            slug="summer-vibes-concert",
            description="An amazing summer concert featuring top artists.",
            start_date=now + timedelta(days=10),
            end_date=now + timedelta(days=10, hours=4),
            is_published=True,
            capacity=venue1.capacity,
        )
        self.stdout.write("Adding images to Summer Vibes Concert...")
        attach_seed_image(event1, "summer_vibes_main.png", is_primary=True)

        event2 = Event.objects.create(
            organizer=org1.organizer_profile,
            category=cat_tech,
            venue=venue2,
            title="Tech Future Summit",
            slug="tech-future-summit",
            description="Explore the future of technology.",
            start_date=now + timedelta(days=20),
            end_date=now + timedelta(days=22),
            is_published=True,
            capacity=venue2.capacity,
        )
        self.stdout.write("Adding images to Tech Future Summit...")
        attach_seed_image(event2, "tech_future_main.png", is_primary=True)

        event3 = Event.objects.create(
            organizer=org2.organizer_profile,
            category=cat_art,
            venue=venue1,
            title="Modern Art Gala",
            slug="modern-art-gala",
            description="A showcase of modern art masterpieces.",
            start_date=now + timedelta(days=5),
            end_date=now + timedelta(days=5, hours=3),
            is_published=True,
            capacity=venue1.capacity,
        )
        self.stdout.write("Adding images to Modern Art Gala...")
        attach_seed_image(event3, "modern_art_main.png", is_primary=True)

        # Create Ticket Types
        self.stdout.write("Creating ticket types...")
        tt1_vip = TicketType.objects.create(
            event=event1,
            name="VIP",
            price=150.00,
            quantity_total=50,
            sale_start=now - timedelta(days=1),
            sale_end=event1.start_date,
        )
        tt1_ga = TicketType.objects.create(
            event=event1,
            name="General Admission",
            price=50.00,
            quantity_total=450,
            sale_start=now - timedelta(days=1),
            sale_end=event1.start_date,
        )

        tt2_std = TicketType.objects.create(
            event=event2,
            name="Standard Pass",
            price=200.00,
            quantity_total=1000,
            sale_start=now - timedelta(days=5),
            sale_end=event2.start_date,
        )

        tt3_early = TicketType.objects.create(
            event=event3,
            name="Early Bird",
            price=25.00,
            quantity_total=100,
            sale_start=now - timedelta(days=10),
            sale_end=event3.start_date,
        )

        # Create Bookings (Orders)
        self.stdout.write("Creating bookings...")

        # User 1 buys VIP ticket for Event 1
        order1 = Order.objects.create(
            user=user1, event=event1, status="paid", total_amount=tt1_vip.price * 2
        )
        item1 = OrderItem.objects.create(
            order=order1,
            ticket_type=tt1_vip,
            quantity=2,
            price_per_ticket=tt1_vip.price,
        )
        # Generate tickets and attendees
        for i in range(2):
            code = Ticket.generate_unique_code()
            ticket = Ticket.objects.create(ticket_type=tt1_vip, code=code, status="booked")
            tt1_vip.quantity_sold += 1
            tt1_vip.save()
            Attendee.objects.create(
                order_item=item1,
                full_name=f"Attendee {i + 1} User1",
                email=f"attendee{i + 1}@user1.com",
                ticket=ticket,
            )

        # User 2 buys Standard Pass for Event 2
        order2 = Order.objects.create(
            user=user2, event=event2, status="paid", total_amount=tt2_std.price
        )
        item2 = OrderItem.objects.create(
            order=order2,
            ticket_type=tt2_std,
            quantity=1,
            price_per_ticket=tt2_std.price,
        )
        code = Ticket.generate_unique_code()
        ticket = Ticket.objects.create(ticket_type=tt2_std, code=code, status="booked")
        tt2_std.quantity_sold += 1
        tt2_std.save()
        Attendee.objects.create(
            order_item=item2,
            full_name="Attendee User2",
            email="attendee@user2.com",
            ticket=ticket,
        )

        self.stdout.write(self.style.SUCCESS("Database populated successfully!"))
