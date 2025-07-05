import sqlite3

DB_PATH = "/home/matheus/RaspMIDI/data/midi_config.db"  # ajuste o caminho se necessário

expected_schema = {
    "patches": [
        "id", "name", "effects", "input_device", "input_channel", "output_device", "command_type",
        "zoom_bank", "zoom_patch", "zoom_bank_letter", "program", "cc", "value", "note", "velocity",
        "created_at", "updated_at"
    ],
    "effects": [
        "id", "name", "cc_number", "enabled", "parameters"
    ],
    "midi_commands": [
        "id", "type", "channel", "note", "cc", "value", "timestamp"
    ],
    "banks": [
        "id", "name", "description", "active", "created_at", "updated_at"
    ],
    "bank_mappings": [
        "id", "bank_id", "input_type", "input_channel", "input_control", "input_value",
        "output_device", "output_type", "output_channel", "output_control", "output_value",
        "output_program", "description"
    ],
    "zoom_patches": [
        "id", "bank", "number", "name", "updated_at"
    ]
}

def get_table_columns(cursor, table):
    cursor.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cursor.fetchall()]

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    all_ok = True

    for table, expected_cols in expected_schema.items():
        print(f"\nTabela: {table}")
        try:
            cols = get_table_columns(cursor, table)
            print(f"  Campos no banco:    {cols}")
            print(f"  Campos esperados:   {expected_cols}")

            missing = [c for c in expected_cols if c not in cols]
            extra = [c for c in cols if c not in expected_cols]

            if not missing and not extra:
                print("  ✅ Estrutura OK!")
            else:
                all_ok = False
                if missing:
                    print(f"  ❌ Faltando no banco: {missing}")
                if extra:
                    print(f"  ⚠️  Extras no banco: {extra}")
        except Exception as e:
            all_ok = False
            print(f"  ❌ Erro ao validar tabela: {e}")

    if all_ok:
        print("\nTudo certo! Todas as tabelas estão de acordo com o modelo esperado.")
    else:
        print("\nAtenção: Algumas tabelas estão diferentes do modelo esperado. Veja acima.")

if __name__ == "__main__":
    main()
