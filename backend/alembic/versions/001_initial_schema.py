"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('phone', sa.String(20), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=True, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, default='organizer'),
        sa.Column('verified_phone', sa.Boolean(), nullable=False, default=False),
        sa.Column('verified_email', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_users_phone', 'users', ['phone'])
    op.create_index('ix_users_email', 'users', ['email'])

    # Venues table
    op.create_table(
        'venues',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('location_json', postgresql.JSONB(), nullable=False),
        sa.Column('owner_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('policies_json', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Courts table
    op.create_table(
        'courts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('venue_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('venues.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('sport', sa.String(50), nullable=False),
        sa.Column('attributes_json', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Slots table
    op.create_table(
        'slots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('court_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('courts.id'), nullable=False),
        sa.Column('start_ts', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_ts', sa.DateTime(timezone=True), nullable=False),
        sa.Column('price_cents', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(3), default='USD', nullable=False),
        sa.Column('status', sa.String(20), default='open', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_unique_constraint('uq_slot_court_time', 'slots', ['court_id', 'start_ts', 'end_ts'])
    op.create_index('idx_slot_court_status', 'slots', ['court_id', 'status'])
    op.create_index('idx_slot_time_range', 'slots', ['start_ts', 'end_ts'])

    # Reservations table
    op.create_table(
        'reservations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('slot_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('slots.id'), nullable=False),
        sa.Column('booked_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('actor_type', sa.String(20), nullable=False),
        sa.Column('actor_id', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), default='pending', nullable=False),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payments.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Payments table
    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('provider_ref', sa.String(255), nullable=True),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(3), default='USD', nullable=False),
        sa.Column('status', sa.String(20), default='initiated', nullable=False),
        sa.Column('reservation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('reservations.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Payment events table
    op.create_table(
        'payment_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payments.id'), nullable=True),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('provider_event_id', sa.String(255), nullable=False),
        sa.Column('payload_json', postgresql.JSONB(), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_unique_constraint('uq_payment_event_provider_id', 'payment_events', ['provider', 'provider_event_id'])
    op.create_index('idx_payment_event_provider', 'payment_events', ['provider', 'provider_event_id'])

    # Matches table
    op.create_table(
        'matches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('reservation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('reservations.id'), nullable=False, unique=True),
        sa.Column('sport', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), default='scheduled', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finalized_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Referee assignments table
    op.create_table(
        'referee_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('match_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('matches.id'), nullable=False),
        sa.Column('referee_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('status', sa.String(20), default='offered', nullable=False),
        sa.Column('offered_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Match events table
    op.create_table(
        'match_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('match_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('matches.id'), nullable=False),
        sa.Column('seq', sa.Integer(), nullable=False),
        sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('payload_json', postgresql.JSONB(), nullable=False),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_unique_constraint('uq_match_event_seq', 'match_events', ['match_id', 'seq'])
    op.create_index('idx_match_event_match_seq', 'match_events', ['match_id', 'seq'])

    # Match reports table
    op.create_table(
        'match_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('match_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('matches.id'), nullable=False),
        sa.Column('version', sa.Integer(), default=1, nullable=False),
        sa.Column('status', sa.String(20), default='generating', nullable=False),
        sa.Column('pdf_url', sa.String(500), nullable=True),
        sa.Column('checksum', sa.String(64), nullable=True),
        sa.Column('report_json', postgresql.JSONB(), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_unique_constraint('uq_match_report_version', 'match_reports', ['match_id', 'version'])
    op.create_index('idx_match_report_match_version', 'match_reports', ['match_id', 'version'])

    # Match awards table
    op.create_table(
        'match_awards',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('match_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('matches.id'), nullable=False),
        sa.Column('kind', sa.String(20), nullable=False),
        sa.Column('winner_ref', sa.String(255), nullable=False),
        sa.Column('decided_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('decided_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # PT requests table
    op.create_table(
        'pt_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('scope', sa.String(20), nullable=False),
        sa.Column('requester_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('pt_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('match_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('matches.id'), nullable=True),
        sa.Column('reservation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('reservations.id'), nullable=True),
        sa.Column('details', postgresql.JSONB(), nullable=False),
        sa.Column('status', sa.String(20), default='open', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_pt_request_pt_status', 'pt_requests', ['pt_user_id', 'status'])
    op.create_index('idx_pt_request_requester', 'pt_requests', ['requester_user_id'])

    # Advertisers table
    op.create_table(
        'advertisers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('contact_json', postgresql.JSONB(), nullable=False),
        sa.Column('status', sa.String(20), default='active', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Ad creatives table
    op.create_table(
        'ad_creatives',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('advertiser_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('advertisers.id'), nullable=False),
        sa.Column('media_url', sa.String(500), nullable=False),
        sa.Column('copy', sa.String(1000), nullable=True),
        sa.Column('status', sa.String(20), default='draft', nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decided_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.String(500), nullable=True),
    )

    # Ad placements table
    op.create_table(
        'ad_placements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('match_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('matches.id'), nullable=False),
        sa.Column('slot', sa.String(20), nullable=False),
        sa.Column('creative_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ad_creatives.id'), nullable=False),
        sa.Column('status', sa.String(20), default='scheduled', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_ad_placement_match_slot', 'ad_placements', ['match_id', 'slot'])

    # Player profiles table
    op.create_table(
        'player_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('photo_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_player_profiles_phone', 'player_profiles', ['phone'])

    # Squads table
    op.create_table(
        'squads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('team_name', sa.String(255), nullable=False),
        sa.Column('sport', sa.String(50), nullable=False),
        sa.Column('owner_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Squad members table
    op.create_table(
        'squad_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('squad_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('squads.id'), nullable=False),
        sa.Column('player_profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('player_profiles.id'), nullable=False),
        sa.Column('jersey_no', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_squad_member_squad', 'squad_members', ['squad_id'])

    # Formations table
    op.create_table(
        'formations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('match_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('matches.id'), nullable=True),
        sa.Column('squad_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('squads.id'), nullable=True),
        sa.Column('shape', sa.String(50), nullable=False),
        sa.Column('positions_json', postgresql.JSONB(), nullable=False),
        sa.Column('share_token', sa.String(64), nullable=False, unique=True),
        sa.Column('share_permission', sa.String(20), default='view', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_formations_share_token', 'formations', ['share_token'])
    op.create_index('idx_formation_match', 'formations', ['match_id'])
    op.create_index('idx_formation_squad', 'formations', ['squad_id'])


def downgrade() -> None:
    op.drop_table('formations')
    op.drop_table('squad_members')
    op.drop_table('squads')
    op.drop_table('player_profiles')
    op.drop_table('ad_placements')
    op.drop_table('ad_creatives')
    op.drop_table('advertisers')
    op.drop_table('pt_requests')
    op.drop_table('match_awards')
    op.drop_table('match_reports')
    op.drop_table('match_events')
    op.drop_table('referee_assignments')
    op.drop_table('matches')
    op.drop_table('payment_events')
    op.drop_table('payments')
    op.drop_table('reservations')
    op.drop_table('slots')
    op.drop_table('courts')
    op.drop_table('venues')
    op.drop_table('users')

