-- Remove coluna telefone_celular da tabela clientes_finais
-- Mantém apenas whatsapp para disparos

-- Verificar se a coluna existe antes de remover
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'clientes_finais'
        AND column_name = 'telefone_celular'
    ) THEN
        ALTER TABLE clientes_finais DROP COLUMN telefone_celular;
        RAISE NOTICE 'Coluna telefone_celular removida com sucesso';
    ELSE
        RAISE NOTICE 'Coluna telefone_celular já não existe';
    END IF;
END $$;
