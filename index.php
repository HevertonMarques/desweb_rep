<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>DevTrack System - Gestão e Perfis de Acesso</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: {
              50: '#f0f3ff',
              100: '#e0e7ff',
              500: '#6366f1',
              600: '#4f46e5',
              700: '#4338ca',
              900: '#312e81',
            }
          }
        }
      }
    }
  </script>
  <style>
    .custom-scrollbar::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
      background: transparent;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
      background: rgba(156, 163, 175, 0.3);
      border-radius: 3px;
    }
  </style>
</head>
<body class="bg-slate-900 text-slate-100 font-sans antialiased min-h-screen flex flex-col transition-colors duration-200" id="app-body">

  <div class="flex flex-1 overflow-hidden h-screen">

    <!-- Mobile Overlay -->
    <div id="sidebar-backdrop" onclick="toggleSidebar()" class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-40 hidden md:hidden"></div>

    <!-- Sidebar Component -->
    <aside id="sidebar" class="fixed md:static inset-y-0 left-0 z-50 w-72 bg-slate-950 border-r border-slate-800/80 flex flex-col transform -translate-x-full md:translate-x-0 transition-transform duration-300 ease-in-out shrink-0">
      
      <!-- App Header -->
      <div class="p-4 border-b border-slate-800/80 flex items-center justify-between">
        <div class="flex items-center gap-3 min-w-0">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-400 flex items-center justify-center text-white shadow-lg shadow-indigo-500/20 shrink-0">
            <i class="fa-solid fa-square-poll-vertical text-lg"></i>
          </div>
          <div class="min-w-0">
            <span class="font-bold text-slate-100 text-base block truncate">DevTrack System</span>
            <span class="text-xs text-slate-400 block truncate">Controle & Registros</span>
          </div>
        </div>
        <button onclick="toggleSidebar()" class="md:hidden text-slate-400 hover:text-white p-2">
          <i class="fa-solid fa-xmark text-lg"></i>
        </button>
      </div>

      <!-- System Details Card -->
      <div class="p-4 mx-3 my-3 bg-slate-900/90 rounded-xl border border-slate-800/80 flex items-center gap-3 min-w-0">
        <div class="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center shrink-0">
          <i class="fa-solid fa-code text-sm"></i>
        </div>
        <div class="min-w-0 flex-1">
          <div class="text-xs font-semibold text-slate-200 truncate">DevTrack System</div>
          <div class="text-[11px] text-slate-400 truncate">v2.5 • Controle de Níveis</div>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 px-3 py-2 space-y-1 overflow-y-auto custom-scrollbar">
        <button onclick="switchTab('dashboard')" id="nav-dashboard" class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all bg-indigo-600 text-white shadow-lg shadow-indigo-600/20">
          <i class="fa-solid fa-chart-pie w-5 text-center"></i>
          <span class="truncate">Dashboard</span>
        </button>

        <button onclick="switchTab('projects')" id="nav-projects" class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all text-slate-400 hover:text-slate-200 hover:bg-slate-900">
          <i class="fa-solid fa-folder-open w-5 text-center"></i>
          <span class="truncate">Projetos & Aulas</span>
        </button>

        <button onclick="switchTab('tasks')" id="nav-tasks" class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all text-slate-400 hover:text-slate-200 hover:bg-slate-900">
          <i class="fa-solid fa-list-check w-5 text-center"></i>
          <span class="truncate">Tarefas & Entregas</span>
        </button>

        <button onclick="switchTab('editor')" id="nav-editor" class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all text-slate-400 hover:text-slate-200 hover:bg-slate-900">
          <i class="fa-solid fa-code w-5 text-center"></i>
          <span class="truncate">Editor & Docs</span>
        </button>

        <button onclick="switchTab('profile')" id="nav-profile" class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all text-slate-400 hover:text-slate-200 hover:bg-slate-900">
          <i class="fa-solid fa-graduation-cap w-5 text-center"></i>
          <span class="truncate">Perfil & Nível de Acesso</span>
        </button>
      </nav>

      <!-- Repo Reference Card -->
      <div class="p-3 mx-3 mb-3 bg-slate-900/60 rounded-xl border border-slate-800/60">
        <div class="flex items-center gap-2 mb-2 text-slate-300">
          <i class="fa-brands fa-github text-base"></i>
          <span class="text-xs font-semibold truncate">Repositório Base</span>
        </div>
        <p class="text-[11px] text-slate-400 truncate mb-2">HevertonMarques/desweb_rep</p>
        <a href="https://github.com/HevertonMarques/desweb_rep" target="_blank" class="w-full flex items-center justify-center gap-2 py-1.5 px-3 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium transition-colors">
          <span>Ver no GitHub</span>
          <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
        </a>
      </div>

      <!-- Active Profile Indicator -->
      <div class="p-3 border-t border-slate-800/80 flex items-center justify-between gap-2 min-w-0">
        <div class="flex items-center gap-2.5 min-w-0 flex-1">
          <div class="relative shrink-0">
            <div id="user-avatar" class="w-9 h-9 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold text-xs">
              ED
            </div>
            <span class="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-500 rounded-full border-2 border-slate-950"></span>
          </div>
          <div class="min-w-0 flex-1">
            <div id="user-name" class="text-xs font-semibold text-slate-200 truncate">Estudante Dev</div>
            <div id="user-role-badge" class="text-[10px] text-indigo-400 font-medium truncate">
              Perfil: Aluno
            </div>
          </div>
        </div>
        <button onclick="toggleTheme()" id="theme-toggle-btn" class="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-900 rounded-lg transition-colors shrink-0" title="Alternar Tema">
          <i class="fa-solid fa-moon text-sm"></i>
        </button>
      </div>

    </aside>

    <!-- Main Content Area -->
    <main class="flex-1 flex flex-col min-w-0 overflow-hidden bg-slate-900">
      
      <!-- Top Navbar Mobile / Header -->
      <header class="h-16 border-b border-slate-800/80 px-4 md:px-6 flex items-center justify-between gap-4 shrink-0 bg-slate-950/40 backdrop-blur-md">
        <div class="flex items-center gap-3">
          <button onclick="toggleSidebar()" class="md:hidden p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800">
            <i class="fa-solid fa-bars text-lg"></i>
          </button>
          <h1 id="page-title" class="text-lg md:text-xl font-bold text-slate-100 truncate">Painel de Controle e Registros</h1>
        </div>

        <!-- Role Selector Switcher -->
        <div class="flex items-center gap-3">
          <div class="flex items-center bg-slate-950 border border-slate-800 rounded-lg p-1 text-xs">
            <span class="text-slate-400 px-2 hidden sm:inline"><i class="fa-solid fa-user-shield mr-1"></i> Acesso:</span>
            <select id="role-selector" onchange="changeRole(this.value)" class="bg-slate-900 text-slate-200 font-medium rounded px-2 py-1 focus:outline-none text-xs border border-slate-800">
              <option value="student">Aluno (Restrito)</option>
              <option value="teacher">Prof. André Marcos (Docente)</option>
              <option value="admin">Administrador (Total)</option>
            </select>
          </div>

          <button onclick="exportReport()" id="btn-report" class="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700/80 transition-colors">
            <i class="fa-solid fa-file-arrow-down text-indigo-400"></i>
            <span>Relatório</span>
          </button>

          <button onclick="openNewModal()" id="btn-new-entry" class="flex items-center gap-2 px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg shadow-lg shadow-indigo-600/20 transition-all">
            <i class="fa-solid fa-plus"></i>
            <span class="hidden sm:inline">Nova Entrega</span>
          </button>
        </div>
      </header>

      <!-- Dynamic Views Container -->
      <div class="flex-1 overflow-y-auto p-4 md:p-6 custom-scrollbar" id="content-area">

        <!-- DASHBOARD VIEW -->
        <div id="view-dashboard" class="space-y-6">
          
          <!-- Key Metrics -->
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 flex items-center justify-between">
              <div>
                <span class="text-xs font-medium text-slate-400 block mb-1">Total de Entregas</span>
                <span class="text-2xl font-bold text-slate-100" id="metric-total">12</span>
              </div>
              <div class="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center text-lg">
                <i class="fa-solid fa-box-archive"></i>
              </div>
            </div>

            <div class="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 flex items-center justify-between">
              <div>
                <span class="text-xs font-medium text-slate-400 block mb-1">Concluídas</span>
                <span class="text-2xl font-bold text-emerald-400" id="metric-completed">9</span>
              </div>
              <div class="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center text-lg">
                <i class="fa-solid fa-circle-check"></i>
              </div>
            </div>

            <div class="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 flex items-center justify-between">
              <div>
                <span class="text-xs font-medium text-slate-400 block mb-1">Em Pendência</span>
                <span class="text-2xl font-bold text-amber-400" id="metric-pending">3</span>
              </div>
              <div class="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center text-lg">
                <i class="fa-solid fa-clock-rotate-left"></i>
              </div>
            </div>

            <div class="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 flex items-center justify-between">
              <div>
                <span class="text-xs font-medium text-slate-400 block mb-1">Média do Progresso</span>
                <span class="text-2xl font-bold text-indigo-400">85%</span>
              </div>
              <div class="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center text-lg">
                <i class="fa-solid fa-chart-line"></i>
              </div>
            </div>
          </div>

          <!-- Main Grid -->
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            <!-- Progress breakdown -->
            <div class="lg:col-span-2 bg-slate-950/60 p-5 rounded-xl border border-slate-800/80 space-y-4">
              <div class="flex items-center justify-between">
                <h2 class="text-base font-bold text-slate-100 flex items-center gap-2">
                  <i class="fa-solid fa-list-progress text-indigo-400"></i>
                  <span>Status por Categoria de Registro</span>
                </h2>
                <span class="text-xs text-slate-400">Atualizado recentemente</span>
              </div>

              <div class="space-y-4 pt-2">
                <div>
                  <div class="flex justify-between text-xs font-medium mb-1">
                    <span class="text-slate-300">Desenvolvimento Web Basic (HTML/CSS)</span>
                    <span class="text-emerald-400">100%</span>
                  </div>
                  <div class="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div class="bg-emerald-500 h-full rounded-full" style="width: 100%"></div>
                  </div>
                </div>

                <div>
                  <div class="flex justify-between text-xs font-medium mb-1">
                    <span class="text-slate-300">JavaScript Interativo & DOM</span>
                    <span class="text-indigo-400">80%</span>
                  </div>
                  <div class="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div class="bg-indigo-500 h-full rounded-full" style="width: 80%"></div>
                  </div>
                </div>

                <div>
                  <div class="flex justify-between text-xs font-medium mb-1">
                    <span class="text-slate-300">Frameworks & Tailwind CSS</span>
                    <span class="text-indigo-400">75%</span>
                  </div>
                  <div class="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                    <div class="bg-indigo-500 h-full rounded-full" style="width: 75%"></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Quick Tasks -->
            <div class="bg-slate-950/60 p-5 rounded-xl border border-slate-800/80 space-y-4">
              <div class="flex items-center justify-between">
                <h2 class="text-base font-bold text-slate-100 flex items-center gap-2">
                  <i class="fa-solid fa-fire text-amber-400"></i>
                  <span>Lembretes Rápidos</span>
                </h2>
              </div>

              <div class="space-y-2.5" id="quick-tasks-list">
                <div class="flex items-center justify-between p-2.5 bg-slate-900 rounded-lg border border-slate-800 text-xs">
                  <div class="flex items-center gap-2.5">
                    <input type="checkbox" checked class="rounded border-slate-700 text-indigo-600 focus:ring-0 bg-slate-800">
                    <span class="line-through text-slate-500">Enviar protótipo v2.5</span>
                  </div>
                  <span class="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-medium">Feito</span>
                </div>
              </div>

              <div class="pt-2">
                <div class="flex gap-2">
                  <input type="text" id="quick-task-input" placeholder="Novo lembrete..." class="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500">
                  <button onclick="addQuickTask()" class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-lg transition-colors">
                    Add
                  </button>
                </div>
              </div>
            </div>

          </div>

        </div>

        <!-- PROJECTS VIEW -->
        <div id="view-projects" class="space-y-6 hidden">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
            <div>
              <h2 class="text-base font-bold text-slate-100">Registros de Projetos & Atividades</h2>
              <p class="text-xs text-slate-400">Repositório de códigos e entregas práticas</p>
            </div>
            <div class="flex items-center gap-2">
              <input type="text" id="search-projects" onkeyup="filterProjects()" placeholder="Buscar registro..." class="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 w-full sm:w-48">
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" id="projects-grid">
            <!-- Dynamic projects -->
          </div>
        </div>

        <!-- TASKS VIEW -->
        <div id="view-tasks" class="space-y-6 hidden">
          <div class="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 flex items-center justify-between">
            <h2 class="text-base font-bold text-slate-100">Tabela de Controle de Registros</h2>
            <span class="text-xs text-slate-400">Acompanhamento por Nível de Acesso</span>
          </div>

          <div class="bg-slate-950/60 rounded-xl border border-slate-800/80 overflow-hidden">
            <div class="overflow-x-auto">
              <table class="w-full text-left text-xs">
                <thead class="bg-slate-900 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th class="p-3.5">Título / Atividade</th>
                    <th class="p-3.5">Categoria</th>
                    <th class="p-3.5">Data limite</th>
                    <th class="p-3.5">Status</th>
                    <th class="p-3.5 text-right action-col">Ação</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-800/60 text-slate-300" id="tasks-table-body">
                  <!-- Dynamic tasks -->
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- EDITOR VIEW -->
        <div id="view-editor" class="h-full flex flex-col space-y-4 hidden">
          <div class="flex items-center justify-between bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
            <div class="flex items-center gap-2">
              <i class="fa-solid fa-code text-indigo-400"></i>
              <span class="text-xs font-bold text-slate-200">Playground de Teste em Tempo Real</span>
            </div>
            <button onclick="runCode()" class="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5">
              <i class="fa-solid fa-play text-[10px]"></i>
              <span>Executar Código</span>
            </button>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1 min-h-[400px]">
            <div class="flex flex-col bg-slate-950 rounded-xl border border-slate-800/80 overflow-hidden">
              <div class="bg-slate-900 px-3 py-2 border-b border-slate-800 text-xs font-mono text-slate-400 flex items-center justify-between">
                <span>HTML / Tailwind Preview</span>
                <span class="text-[10px] text-slate-500">Live Editor</span>
              </div>
              <textarea id="code-input" class="flex-1 bg-slate-950 text-slate-200 font-mono text-xs p-3 focus:outline-none resize-none custom-scrollbar" spellcheck="false"><div class="p-4 bg-indigo-950/40 border border-indigo-500/30 rounded-xl text-center">
  <h2 class="text-indigo-400 font-bold text-base mb-1">DevTrack System - Teste</h2>
  <p class="text-xs text-slate-300">Protótipo interativo com níveis de acesso!</p>
</div></textarea>
            </div>

            <div class="flex flex-col bg-slate-950 rounded-xl border border-slate-800/80 overflow-hidden">
              <div class="bg-slate-900 px-3 py-2 border-b border-slate-800 text-xs font-mono text-slate-400 flex items-center justify-between">
                <span>Resultado Visual</span>
                <span class="text-[10px] text-emerald-400">Output</span>
              </div>
              <iframe id="code-output" class="flex-1 w-full bg-slate-900/50"></iframe>
            </div>
          </div>
        </div>

        <!-- PROFILE VIEW -->
        <div id="view-profile" class="space-y-6 hidden">
          <div class="bg-slate-950/60 p-6 rounded-xl border border-slate-800/80 flex flex-col md:flex-row items-center gap-6">
            <div id="profile-avatar-large" class="w-20 h-20 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center text-white text-2xl font-bold shadow-xl shadow-indigo-500/20 shrink-0">
              ED
            </div>
            <div class="space-y-1 text-center md:text-left flex-1 min-w-0">
              <h2 id="profile-name-large" class="text-xl font-bold text-slate-100">Estudante Dev</h2>
              <p id="profile-role-description" class="text-xs text-indigo-400">Desenvolvimento Web • Perfil: Aluno (Restrito)</p>
              <p class="text-xs text-slate-400 pt-1">Nível de permissão selecionado dinamicamente para demonstração.</p>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-slate-950/60 p-5 rounded-xl border border-slate-800/80 space-y-3">
              <h3 class="text-sm font-bold text-slate-200 border-b border-slate-800 pb-2">Permissões do Perfil Atual</h3>
              <ul class="text-xs space-y-2 text-slate-300" id="role-permissions-list">
                <!-- Permissions injected by JS -->
              </ul>
            </div>

            <div class="bg-slate-950/60 p-5 rounded-xl border border-slate-800/80 space-y-3">
              <h3 class="text-sm font-bold text-slate-200 border-b border-slate-800 pb-2">Informações da Disciplina</h3>
              <ul class="text-xs space-y-2 text-slate-300">
                <li class="flex justify-between"><span class="text-slate-500">Curso:</span> <span>Desenvolvimento Web</span></li>
                <li class="flex justify-between"><span class="text-slate-500">Docente:</span> <span>Prof. André Marcos</span></li>
                <li class="flex justify-between"><span class="text-slate-500">Sistema:</span> <span>DevTrack System v2.5</span></li>
              </ul>
            </div>
          </div>
        </div>

      </div>

    </main>

  </div>

  <!-- Modal Nova Entrega -->
  <div id="modal-new" class="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 hidden">
    <div class="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-5 space-y-4 shadow-2xl">
      <div class="flex items-center justify-between border-b border-slate-800 pb-3">
        <h3 class="text-base font-bold text-slate-100">Registar Nova Entrega</h3>
        <button onclick="closeNewModal()" class="text-slate-400 hover:text-white">
          <i class="fa-solid fa-xmark text-lg"></i>
        </button>
      </div>

      <div class="space-y-3">
        <div>
          <label class="text-xs font-medium text-slate-300 block mb-1">Título do Registro</label>
          <input type="text" id="modal-title" placeholder="Ex: Exercício 04 - DOM JS" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500">
        </div>

        <div>
          <label class="text-xs font-medium text-slate-300 block mb-1">Categoria</label>
          <select id="modal-category" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500">
            <option value="HTML/CSS">HTML / CSS</option>
            <option value="JavaScript">JavaScript</option>
            <option value="Projeto">Projeto Prático</option>
          </select>
        </div>

        <div>
          <label class="text-xs font-medium text-slate-300 block mb-1">Status</label>
          <select id="modal-status" class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500">
            <option value="Concluído">Concluído</option>
            <option value="Pendente">Pendente</option>
          </select>
        </div>
      </div>

      <div class="flex justify-end gap-2 pt-2 border-t border-slate-800">
        <button onclick="closeNewModal()" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg transition-colors">
          Cancelar
        </button>
        <button onclick="saveNewProject()" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg transition-colors">
          Salvar Registro
        </button>
      </div>
    </div>
  </div>

  <script>
    // State Data
    let currentRole = 'student'; // 'student', 'teacher', 'admin'

    let projectsData = [
      { id: 1, title: "Exercício 01 - Estrutura HTML5", category: "HTML/CSS", status: "Concluído", date: "10/02/2026", desc: "Criação de marcas e formulários semânticos." },
      { id: 2, title: "Exercício 02 - Estilização CSS Grid", category: "HTML/CSS", status: "Concluído", date: "17/02/2026", desc: "Layouts responsivos com CSS Grid e Flexbox." },
      { id: 3, title: "Exercício 03 - Eventos e DOM JS", category: "JavaScript", status: "Concluído", date: "24/02/2026", desc: "Manipulação de elementos e captura de cliques." },
      { id: 4, title: "Projeto Dashboard DevTrack", category: "Projeto", status: "Concluído", date: "03/03/2026", desc: "Interface interativa de acompanhamento de tarefas." },
      { id: 5, title: "Exercício 04 - Fetch API & Async", category: "JavaScript", status: "Pendente", date: "15/03/2026", desc: "Consumo de dados assíncronos e tratamento de erros." },
    ];

    let isDarkTheme = true;

    // Change Role System
    function changeRole(role) {
      currentRole = role;
      
      const avatar = document.getElementById('user-avatar');
      const avatarLarge = document.getElementById('profile-avatar-large');
      const userName = document.getElementById('user-name');
      const userNameLarge = document.getElementById('profile-name-large');
      const roleBadge = document.getElementById('user-role-badge');
      const roleDesc = document.getElementById('profile-role-description');
      const permissionsList = document.getElementById('role-permissions-list');
      const btnNewEntry = document.getElementById('btn-new-entry');

      if (role === 'admin') {
        avatar.innerText = 'AD';
        avatarLarge.innerText = 'AD';
        userName.innerText = 'Administrador';
        userNameLarge.innerText = 'Administrador do Sistema';
        roleBadge.innerText = 'Perfil: Admin (Acesso Total)';
        roleBadge.className = 'text-[10px] text-red-400 font-semibold truncate';
        roleDesc.innerText = 'Acesso irrestrito a configurações, exclusão de dados e relatórios gerais.';
        
        permissionsList.innerHTML = `
          <li class="flex items-center gap-2 text-emerald-400"><i class="fa-solid fa-check"></i> Gestão de usuários e turmas</li>
          <li class="flex items-center gap-2 text-emerald-400"><i class="fa-solid fa-check"></i> Exclusão e edição de registros de qualquer aluno</li>
          <li class="flex items-center gap-2 text-emerald-400"><i class="fa-solid fa-check"></i> Exportação de relatórios gerais</li>
          <li class="flex items-center gap-2 text-emerald-400"><i class="fa-solid fa-check"></i> Acesso ao Playground e Logs</li>
        `;
        btnNewEntry.classList.remove('hidden');
      } else if (role === 'teacher') {
        avatar.innerText = 'AM';
        avatarLarge.innerText = 'AM';
        userName.innerText = 'Prof. André Marcos';
        userNameLarge.innerText = 'Prof. André Marcos';
        roleBadge.innerText = 'Perfil: Docente / Coordenador';
        roleBadge.className = 'text-[10px] text-amber-400 font-semibold truncate';
        roleDesc.innerText = 'Controle pedagógico, criação de atividades e gestão de notas.';
        
        permissionsList.innerHTML = `
          <li class="flex items-center gap-2 text-emerald-400"><i class="fa-solid fa-check"></i> Cadastro e avaliação de atividades</li>
          <li class="flex items-center gap-2 text-emerald-400"><i class="fa-solid fa-check"></i> Alteração de status das entregas</li>
          <li class="flex items-center gap-2 text-emerald-400"><i class="fa-solid fa-check"></i> Geração de relatórios por turma</li>
          <li class="flex items-center gap-2 text-slate-500"><i class="fa-solid fa-xmark"></i> Exclusão de logs do sistema (Bloqueado)</li>
        `;
        btnNewEntry.classList.remove('hidden');
      } else {
        avatar.innerText = 'ED';
        avatarLarge.innerText = 'ED';
        userName.innerText = 'Estudante Dev';
        userNameLarge.innerText = 'Estudante Dev';
        roleBadge.innerText = 'Perfil: Aluno (Restrito)';
        roleBadge.className = 'text-[10px] text-indigo-400 font-semibold truncate';
        roleDesc.innerText = 'Visualização de tarefas, envio de trabalhos e playground de código.';
        
        permissionsList.innerHTML = `
          <li class="flex items-center gap-2 text-emerald-400"><i class="fa-solid fa-check"></i> Envio e visualização de entregas próprias</li>
          <li class="flex items-center gap-2 text-emerald-400"><i class="fa-solid fa-check"></i> Acesso ao Playground de teste de código</li>
          <li class="flex items-center gap-2 text-slate-500"><i class="fa-solid fa-xmark"></i> Exclusão de registros (Apenas leitura/envio)</li>
          <li class="flex items-center gap-2 text-slate-500"><i class="fa-solid fa-xmark"></i> Alteração de notas e status globais</li>
        `;
        btnNewEntry.classList.add('hidden'); // Students can't add global tasks directly in restricted mode
      }

      renderData();
    }

    // Sidebar Mobile
    function toggleSidebar() {
      const sidebar = document.getElementById('sidebar');
      const backdrop = document.getElementById('sidebar-backdrop');
      sidebar.classList.toggle('-translate-x-full');
      backdrop.classList.toggle('hidden');
    }

    // Switch Tabs
    function switchTab(tabId) {
      const tabs = ['dashboard', 'projects', 'tasks', 'editor', 'profile'];
      const titles = {
        dashboard: 'Painel de Controle e Registros',
        projects: 'Registros de Projetos & Aulas',
        tasks: 'Controle de Tarefas & Entregas',
        editor: 'Playground & Documentação',
        profile: 'Perfil & Nível de Acesso'
      };

      tabs.forEach(id => {
        const view = document.getElementById(`view-${id}`);
        const nav = document.getElementById(`nav-${id}`);
        
        if (id === tabId) {
          view.classList.remove('hidden');
          nav.className = "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all bg-indigo-600 text-white shadow-lg shadow-indigo-600/20";
        } else {
          view.classList.add('hidden');
          nav.className = "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all text-slate-400 hover:text-slate-200 hover:bg-slate-900";
        }
      });

      document.getElementById('page-title').innerText = titles[tabId];

      if (window.innerWidth < 768) {
        const sidebar = document.getElementById('sidebar');
        if (!sidebar.classList.contains('-translate-x-full')) {
          toggleSidebar();
        }
      }

      if (tabId === 'editor') {
        runCode();
      }
    }

    // Render Data with Role Protection
    function renderData() {
      const grid = document.getElementById('projects-grid');
      const tbody = document.getElementById('tasks-table-body');
      
      grid.innerHTML = '';
      tbody.innerHTML = '';

      let completedCount = 0;

      projectsData.forEach(item => {
        if (item.status === 'Concluído') completedCount++;

        const statusBg = item.status === 'Concluído' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border-amber-500/20';
        
        // Hide delete action for Students
        const deleteButtonHtml = (currentRole === 'admin' || currentRole === 'teacher') 
          ? `<button onclick="deleteProject(${item.id})" class="text-slate-500 hover:text-red-400 transition-colors" title="Excluir Registro"><i class="fa-solid fa-trash"></i></button>`
          : `<span class="text-[10px] text-slate-600"><i class="fa-solid fa-lock"></i> Bloqueado</span>`;

        grid.innerHTML += `
          <div class="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 flex flex-col justify-between space-y-3">
            <div>
              <div class="flex items-center justify-between mb-2">
                <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">${item.category}</span>
                <span class="px-2 py-0.5 rounded text-[10px] font-semibold border ${statusBg}">${item.status}</span>
              </div>
              <h3 class="text-sm font-bold text-slate-100 mb-1">${item.title}</h3>
              <p class="text-xs text-slate-400">${item.desc}</p>
            </div>
            <div class="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-500">
              <span><i class="fa-regular fa-calendar mr-1"></i>${item.date}</span>
              ${deleteButtonHtml}
            </div>
          </div>
        `;

        tbody.innerHTML += `
          <tr class="hover:bg-slate-900/50">
            <td class="p-3.5 font-medium text-slate-200">${item.title}</td>
            <td class="p-3.5 text-slate-400">${item.category}</td>
            <td class="p-3.5 text-slate-400">${item.date}</td>
            <td class="p-3.5"><span class="px-2 py-0.5 rounded text-[10px] font-semibold border ${statusBg}">${item.status}</span></td>
            <td class="p-3.5 text-right action-col">${deleteButtonHtml}</td>
          </tr>
        `;
      });

      document.getElementById('metric-total').innerText = projectsData.length;
      document.getElementById('metric-completed').innerText = completedCount;
      document.getElementById('metric-pending').innerText = projectsData.length - completedCount;
    }

    // Modal Operations
    function openNewModal() {
      document.getElementById('modal-new').classList.remove('hidden');
    }
    function closeNewModal() {
      document.getElementById('modal-new').classList.add('hidden');
    }
    function saveNewProject() {
      const title = document.getElementById('modal-title').value.trim();
      const category = document.getElementById('modal-category').value;
      const status = document.getElementById('modal-status').value;

      if (!title) return alert('Por favor, informe o título da entrega.');

      const newObj = {
        id: Date.now(),
        title,
        category,
        status,
        date: new Date().toLocaleDateString('pt-BR'),
        desc: `Adicionado pelo perfil: ${currentRole.toUpperCase()}`
      };

      projectsData.unshift(newObj);
      renderData();
      closeNewModal();
      document.getElementById('modal-title').value = '';
    }

    function deleteProject(id) {
      if (currentRole === 'student') {
        alert('Acesso negado: Perfil de Aluno não possui permissão para excluir registros.');
        return;
      }
      projectsData = projectsData.filter(p => p.id !== id);
      renderData();
    }

    function addQuickTask() {
      const input = document.getElementById('quick-task-input');
      const val = input.value.trim();
      if (!val) return;

      const list = document.getElementById('quick-tasks-list');
      list.innerHTML += `
        <div class="flex items-center justify-between p-2.5 bg-slate-900 rounded-lg border border-slate-800 text-xs">
          <div class="flex items-center gap-2.5">
            <input type="checkbox" class="rounded border-slate-700 text-indigo-600 focus:ring-0 bg-slate-800">
            <span class="text-slate-300">${val}</span>
          </div>
          <span class="text-[10px] px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 font-medium">Novo</span>
        </div>
      `;
      input.value = '';
    }

    function runCode() {
      const code = document.getElementById('code-input').value;
      const iframe = document.getElementById('code-output');
      const doc = iframe.contentDocument || iframe.contentWindow.document;
      doc.open();
      doc.write(`
        <!DOCTYPE html>
        <html>
        <head>
          <script src="https://cdn.tailwindcss.com"><\/script>
        </head>
        <body class="bg-slate-950 text-slate-100 p-4 font-sans">
          ${code}
        </body>
        </html>
      `);
      doc.close();
    }

    function toggleTheme() {
      const body = document.getElementById('app-body');
      const btnIcon = document.querySelector('#theme-toggle-btn i');
      
      if (isDarkTheme) {
        body.classList.remove('bg-slate-900', 'text-slate-100');
        body.classList.add('bg-slate-100', 'text-slate-900');
        btnIcon.className = "fa-solid fa-sun text-amber-500 text-sm";
      } else {
        body.classList.remove('bg-slate-100', 'text-slate-900');
        body.classList.add('bg-slate-900', 'text-slate-100');
        btnIcon.className = "fa-solid fa-moon text-sm";
      }
      isDarkTheme = !isDarkTheme;
    }

    function exportReport() {
      window.print();
    }

    function filterProjects() {
      const query = document.getElementById('search-projects').value.toLowerCase();
      const cards = document.querySelectorAll('#projects-grid > div');
      cards.forEach(card => {
        const text = card.innerText.toLowerCase();
        card.style.display = text.includes(query) ? 'flex' : 'none';
      });
    }

    window.onload = () => {
      changeRole('student');
    };
  </script>
</body>
</html>
