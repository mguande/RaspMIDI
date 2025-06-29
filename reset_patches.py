#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para resetar e criar patches de exemplo no banco de dados do RaspMIDI
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database.database import get_db, init_db
from app.database.models import Patch
from datetime import datetime

def reset_and_create_patches():
    print("=== RESETANDO PATCHES DO BANCO ===")
    init_db()
    db = get_db()
    if not db:
        print("❌ Banco de dados não disponível")
        return

    # Apaga todos os patches
    print("🗑️ Apagando todos os patches...")
    patches = db.get_all_patches()
    for patch in patches:
        db.delete_patch(patch.id)
    print(f"✅ {len(patches)} patches apagados.")

    # Cria patches de exemplo
    print("➕ Criando patches de exemplo...")
    now = datetime.now().isoformat()
    patches_to_create = [
        Patch(
            name="Clean Channel 1",
            effects={"compressor": {"enabled": True}},
            input_device="Chocolate MIDI",
            input_channel=1,
            output_device="ZOOM G Series",
            command_type="pc",
            zoom_bank=0,
            zoom_patch=1,
            program=1,
            cc=None,
            value=None,
            note=None,
            velocity=None,
            created_at=now,
            updated_at=now
        ),
        Patch(
            name="Crunch Channel 2",
            effects={"overdrive": {"enabled": True}},
            input_device="Chocolate MIDI",
            input_channel=2,
            output_device="ZOOM G Series",
            command_type="pc",
            zoom_bank=1,
            zoom_patch=2,
            program=2,
            cc=None,
            value=None,
            note=None,
            velocity=None,
            created_at=now,
            updated_at=now
        ),
        Patch(
            name="Lead Channel 3",
            effects={"distortion": {"enabled": True}},
            input_device="Chocolate MIDI",
            input_channel=3,
            output_device="ZOOM G Series",
            command_type="pc",
            zoom_bank=2,
            zoom_patch=3,
            program=3,
            cc=None,
            value=None,
            note=None,
            velocity=None,
            created_at=now,
            updated_at=now
        ),
        Patch(
            name="Acoustic Channel 4",
            effects={"reverb": {"enabled": True}},
            input_device="Chocolate MIDI",
            input_channel=4,
            output_device="ZOOM G Series",
            command_type="pc",
            zoom_bank=3,
            zoom_patch=4,
            program=4,
            cc=None,
            value=None,
            note=None,
            velocity=None,
            created_at=now,
            updated_at=now
        ),
        Patch(
            name="Metal Channel 5",
            effects={"distortion": {"enabled": True}},
            input_device="Chocolate MIDI",
            input_channel=5,
            output_device="ZOOM G Series",
            command_type="pc",
            zoom_bank=4,
            zoom_patch=5,
            program=5,
            cc=None,
            value=None,
            note=None,
            velocity=None,
            created_at=now,
            updated_at=now
        ),
    ]

    for patch in patches_to_create:
        db.create_patch(patch)
    print(f"✅ {len(patches_to_create)} patches criados.")

if __name__ == "__main__":
    reset_and_create_patches() 