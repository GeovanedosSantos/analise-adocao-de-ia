import { describe, expect, it } from 'vitest'
import { errosDoServidor, validarCadastro } from './validacao'

const VALIDO = {
  nome: 'Marina',
  email: 'marina@exemplo.com',
  empresa_nome: 'Padaria Aurora',
  empresa_setor: 'Alimentação',
  senha: 'horta-azul-de-julho',
  confirmacao: 'horta-azul-de-julho',
}

describe('validarCadastro', () => {
  it('aceita dados completos', () => {
    expect(validarCadastro(VALIDO)).toEqual({})
  })

  it('aponta cada campo vazio', () => {
    const erros = validarCadastro({ nome: ' ', email: '', empresa_nome: '', empresa_setor: '', senha: '', confirmacao: '' })
    expect(Object.keys(erros).sort()).toEqual(['confirmacao', 'email', 'empresa_nome', 'empresa_setor', 'nome', 'senha'])
  })

  it('recusa e-mail sem domínio', () => {
    expect(validarCadastro({ ...VALIDO, email: 'marina@' }).email).toBe('Informe um e-mail válido.')
  })

  it('recusa senha curta ou só com números', () => {
    expect(validarCadastro({ ...VALIDO, senha: 'abc', confirmacao: 'abc' }).senha).toMatch(/8 caracteres/)
    expect(validarCadastro({ ...VALIDO, senha: '12345678', confirmacao: '12345678' }).senha).toMatch(/só números/)
  })

  it('confere a confirmação', () => {
    expect(validarCadastro({ ...VALIDO, confirmacao: 'outra-senha-qualquer' }).confirmacao).toBe('As senhas não conferem.')
  })
})

describe('errosDoServidor', () => {
  it('distribui as mensagens do DRF nos campos e guarda o detail como erro geral', () => {
    expect(
      errosDoServidor({ email: ['Já existe uma conta com este e-mail.'], senha: ['Muito comum.', 'Muito curta.'], detail: 'Falhou.' }),
    ).toEqual({
      campos: { email: 'Já existe uma conta com este e-mail.', senha: 'Muito comum. Muito curta.' },
      geral: 'Falhou.',
    })
  })

  it('ignora campos desconhecidos e respostas sem corpo', () => {
    expect(errosDoServidor({ outro: ['x'] })).toEqual({ campos: {}, geral: undefined })
    expect(errosDoServidor(null)).toEqual({ campos: {} })
  })
})
