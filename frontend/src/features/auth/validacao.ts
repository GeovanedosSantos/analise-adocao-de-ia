import type { DadosCadastro } from './authApi'

export type CampoCadastro = keyof DadosCadastro | 'confirmacao'
export type ErrosCampos = Partial<Record<CampoCadastro, string>>

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

/**
 * Checagens rápidas antes de enviar. O servidor valida tudo de novo (inclusive senha comum ou
 * parecida com o nome), e os erros dele aparecem nos mesmos campos.
 */
export function validarCadastro(dados: DadosCadastro & { confirmacao: string }): ErrosCampos {
  const erros: ErrosCampos = {}
  if (!dados.nome.trim()) erros.nome = 'Informe seu nome.'
  if (!dados.email.trim()) erros.email = 'Informe seu e-mail.'
  else if (!EMAIL.test(dados.email.trim())) erros.email = 'Informe um e-mail válido.'
  validarEmpresa(dados, erros)
  if (!dados.senha) erros.senha = 'Crie uma senha.'
  else if (dados.senha.length < 8) erros.senha = 'A senha precisa ter pelo menos 8 caracteres.'
  else if (/^\d+$/.test(dados.senha)) erros.senha = 'A senha não pode ter só números.'
  if (!dados.confirmacao) erros.confirmacao = 'Repita a senha.'
  else if (dados.senha && dados.confirmacao !== dados.senha) erros.confirmacao = 'As senhas não conferem.'
  return erros
}

export function validarEmpresa(dados: { empresa_nome: string; empresa_setor: string }, erros: ErrosCampos = {}) {
  if (!dados.empresa_nome.trim()) erros.empresa_nome = 'Informe o nome da empresa.'
  if (!dados.empresa_setor.trim()) erros.empresa_setor = 'Informe o setor da empresa.'
  return erros
}

/** Converte a resposta de erro do DRF ({campo: [mensagens]}) em uma mensagem por campo conhecido. */
export function errosDoServidor(detalhes: unknown): { campos: ErrosCampos; geral?: string } {
  if (!detalhes || typeof detalhes !== 'object') return { campos: {} }
  const campos: ErrosCampos = {}
  let geral: string | undefined
  for (const [chave, valor] of Object.entries(detalhes as Record<string, unknown>)) {
    const mensagem = Array.isArray(valor) ? valor.join(' ') : typeof valor === 'string' ? valor : undefined
    if (!mensagem) continue
    if (CAMPOS.has(chave as CampoCadastro)) campos[chave as CampoCadastro] = mensagem
    else if (chave === 'detail' || chave === 'non_field_errors') geral = mensagem
  }
  return { campos, geral }
}

const CAMPOS = new Set<CampoCadastro>(['nome', 'email', 'senha', 'confirmacao', 'empresa_nome', 'empresa_setor'])

/** Sugestões do campo setor; a pessoa pode escrever outro. */
export const SETORES = [
  'Agronegócio',
  'Alimentação',
  'Construção',
  'Educação',
  'Energia',
  'Financeiro',
  'Indústria',
  'Logística',
  'Saúde',
  'Serviços',
  'Setor público',
  'Tecnologia',
  'Varejo',
]
