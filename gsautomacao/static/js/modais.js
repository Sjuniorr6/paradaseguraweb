// Criar e adicionar os modais ao DOM
document.addEventListener('DOMContentLoaded', function() {
  // Criar o modal do Termo de Responsabilidade
  const termoModal = document.createElement('div');
  termoModal.id = 'termoModal';
  termoModal.className = 'modal';
  termoModal.innerHTML = `
    <div class="modal-content">
      <span class="close">&times;</span>
      <h2>Termo de Responsabilidade</h2>
      <div class="termo-texto">
        <p>1. Ao preencher este formulário, você concorda em fornecer informações verdadeiras e precisas.</p>
        <p>2. Você autoriza o Grupo Golden Sat a entrar em contato através dos meios fornecidos.</p>
        <p>3. Suas informações serão tratadas de acordo com a LGPD.</p>
        <p>4. O Grupo Golden Sat se compromete a não compartilhar seus dados com terceiros.</p>
      </div>
      <div class="termo-acoes">
        <button class="btn-secundario" id="rejeitarTermo">Rejeitar</button>
        <button class="btn-primary" id="aceitarTermo">Aceitar</button>
      </div>
    </div>
  `;

  // Criar o modal do Contrato
  const contratoModal = document.createElement('div');
  contratoModal.id = 'contratoModal';
  contratoModal.className = 'modal';
  contratoModal.innerHTML = `
    <div class="modal-content">
      <span class="close">&times;</span>
      <h2>Contrato de Serviço</h2>
      <div class="termo-texto">
        <p>1. O serviço de rastreamento e monitoramento é fornecido conforme especificações técnicas.</p>
        <p>2. A instalação e manutenção são de responsabilidade do cliente.</p>
        <p>3. O suporte técnico está disponível 24/7.</p>
        <p>4. O contrato pode ser rescindido com aviso prévio de 30 dias.</p>
      </div>
      <div class="termo-acoes">
        <button class="btn-secundario" id="rejeitarContrato">Rejeitar</button>
        <button class="btn-primary" id="aceitarContrato">Aceitar</button>
      </div>
    </div>
  `;

  // Adicionar os modais ao body
  document.body.appendChild(termoModal);
  document.body.appendChild(contratoModal);

  // Gerenciamento dos Modais
  const formulario = document.querySelector('.formulario');
  let formData = null;

  // Função para mostrar modal
  function showModal(modal) {
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
  }

  // Função para fechar modal
  function closeModal(modal) {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
  }

  // Fechar modais ao clicar no X
  document.querySelectorAll('.close').forEach(closeBtn => {
    closeBtn.onclick = function() {
      closeModal(this.closest('.modal'));
    }
  });

  // Fechar modais ao clicar fora
  window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
      closeModal(event.target);
    }
  }

  // Gerenciar formulário
  const spinner = document.getElementById('loadingSpinner');
  const pageSpinner = document.getElementById('pageLoadingSpinner');
  formulario.addEventListener('submit', function(e) {
    e.preventDefault();
    formData = new FormData(this);
    spinner.classList.remove('d-none'); // mostrar spinner do botão
    // NÃO mostrar pageSpinner aqui!
    showModal(termoModal);
  });

  // Gerenciar Termo de Responsabilidade
  document.getElementById('aceitarTermo').addEventListener('click', function() {
    closeModal(termoModal);
    // Após aceitar o termo, mostrar o contrato
    showModal(contratoModal);
  });

  document.getElementById('rejeitarTermo').addEventListener('click', function() {
    closeModal(termoModal);
    alert('É necessário aceitar o termo de responsabilidade para prosseguir.');
  });

  // Gerenciar Contrato
  document.getElementById('aceitarContrato').addEventListener('click', function() {
    closeModal(contratoModal);
    formData.append('aceiteTermo', 'true');
    formData.append('aceiteContrato', 'true');
    if (pageSpinner) pageSpinner.style.display = 'flex'; // mostrar spinner global só aqui
    fetch('/api/salvar-formulario', {
      method: 'POST',
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      if (pageSpinner) pageSpinner.style.display = 'none'; // esconder spinner global
      spinner.classList.add('d-none'); // esconder spinner do botão
      if (data.success) {
        formulario.reset();
        // Exibir toast Bootstrap de sucesso
        const toastEl = document.getElementById('successToast');
        if (toastEl) {
          const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
          toast.show();
        }
      } else {
        throw new Error(data.message || 'Erro ao enviar formulário');
      }
    })
    .catch(error => {
      if (pageSpinner) pageSpinner.style.display = 'none'; // esconder spinner global
      spinner.classList.add('d-none'); // esconder spinner do botão
      console.error('Erro:', error);
      alert('Ocorreu um erro ao enviar o formulário. Por favor, tente novamente.');
    });
  });

  document.getElementById('rejeitarContrato').addEventListener('click', function() {
    closeModal(contratoModal);
    alert('É necessário aceitar o contrato para prosseguir.');
  });

  // Carrossel de produtos atualizado com as imagens fornecidas
  const produtos = [
    {
      titulo: 'Isca Eletrônica',
      descricao: 'Portátil, funciona sem energia do veículo. Ideal para rastreamento em caso de roubos de bens e controle logístico. Disponível em modelo descartável (30 dias) ou retornável ilimitado.',
      imagem: '/isca.png'
    },
    {
      titulo: 'Isca 440',
      descricao: 'Modelo 440: tecnologia avançada para rastreamento seguro e eficiente.',
      imagem: '/isca 440.png'
    },
    {
      titulo: 'Isca 400',
      descricao: 'Modelo 400: robustez e autonomia para rastreamento de cargas.',
      imagem: '/isca 400.png'
    },
    {
      titulo: 'Imobilizador GS',
      descricao: 'Dispositivo para bloqueio remoto do veículo em situações de emergência.',
      imagem: '/Imobilizador.png'
    },
    {
      titulo: 'GS-390',
      descricao: 'Solução compacta para rastreamento discreto.',
      imagem: '/390.png'
    },
    {
      titulo: 'GS-310',
      descricao: 'Ideal para rastreamento de frotas menores e veículos leves.',
      imagem: '/310.png'
    },
    {
      titulo: 'MDVR Veicular',
      descricao: 'Monitoramento com vídeo embarcado e gravação em tempo real.',
      imagem: '/MDVR.png'
    }
  ];
  let produtoAtual = 0;
  const productTitle = document.getElementById('productTitle');
  const productDescription = document.getElementById('productDescription');
  const productImage = document.getElementById('productImage');
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');

  function atualizarProduto(idx) {
    productTitle.textContent = produtos[idx].titulo;
    productDescription.textContent = produtos[idx].descricao;
    productImage.src = produtos[idx].imagem;
  }

  prevBtn.addEventListener('click', function() {
    produtoAtual = (produtoAtual - 1 + produtos.length) % produtos.length;
    atualizarProduto(produtoAtual);
  });
  nextBtn.addEventListener('click', function() {
    produtoAtual = (produtoAtual + 1) % produtos.length;
    atualizarProduto(produtoAtual);
  });

  // Inicializar carrossel
  atualizarProduto(produtoAtual);
}); 