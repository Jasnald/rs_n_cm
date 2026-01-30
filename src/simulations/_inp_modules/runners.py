# _inp_modules/runners.py

from .imports import *
from .dataclasses import *


class AbaqusJobRunner:
    """Executa UM job do Abaqus (Wrapper robusto para Windows)."""
    def __init__(self, config: AbaqusJobConfig):
        self.config = config
        self.scratch_dir = None

        if config.use_scratch:
            self.scratch_dir = Path(config.output_dir) / "scratch"
            # Garante que a pasta existe
            self.scratch_dir.mkdir(parents=True, exist_ok=True)

    def _build_command_string(self) -> str:
        """
        Monta o comando como uma string única para usar shell=True.
        Isso evita problemas de aspas com o .bat do Abaqus.
        """
        # Aspas no comando e no input file são essenciais para caminhos com espaço
        cmd_parts = [
            f'"{self.config.abaqus_cmd}"',
            f'job={self.config.job_name}',
            f'input="{self.config.input_file}"',
            f'cpus={self.config.n_cpus}',
            f'memory={self.config.memory}',
        ]

        if self.scratch_dir:
            # Aspas no scratch também
            cmd_parts.append(f'scratch="{self.scratch_dir}"')

        if self.config.interactive:
            cmd_parts.append("interactive")

        return " ".join(cmd_parts)

    def run(self) -> Tuple[int, float, str]:
        """
        Executa o job.
        Retorna: (return_code, duration, error_msg)
        """
        cmd = self._build_command_string()
        start_time = time.time()

        try:
            # Execução Híbrida: shell=True para compatibilidade
            result = subprocess.run(
                cmd,
                cwd=self.config.output_dir,
                shell=True,  # Mais seguro para Abaqus no Windows
                capture_output=self.config.silent_mode,  # Controla se esconde output
                text=True,
                timeout=self.config.timeout
            )
            duration = time.time() - start_time

            # Se for silencioso, retornamos o erro capturado.
            # Se não for, o erro já apareceu na tela, retornamos vazio ou capturamos se possível.
            err_msg = ""
            if self.config.silent_mode and result.returncode != 0:
                err_msg = result.stderr

            # Limpeza Automática (Sucesso apenas)
            if self.config.auto_cleanup and result.returncode == 0:
                self.cleanup()

            return result.returncode, duration, err_msg

        except subprocess.TimeoutExpired:
            return -1, time.time() - start_time, "TIMEOUT EXPIRED"

        except Exception as e:
            return -2, time.time() - start_time, str(e)

    def cleanup(self):
        """Limpa arquivos temporários da pasta scratch."""
        if self.scratch_dir and self.scratch_dir.exists():
            try:
                shutil.rmtree(self.scratch_dir)
            except OSError:
                pass  # Não falha o job se não conseguir deletar lixo


class AbaqusScriptRunner:

    def __init__(self, config: AbaqusScriptConfig):
        self.config = config

    def run(self) -> int:
        # MUDANÇA: Removi as aspas de {self.config.python_cmd}
        # Isso permite passar algo como: '"C:\Path\abq.bat" python'
        cmd = f'{self.config.python_cmd}"{self.config.script_name}"'

        print(f"Executing Script: {cmd}")
        return subprocess.run(
            cmd,
            shell = True,
            cwd   = self.config.working_dir,
            env   = self.config.env
        ).returncode

class INPRunner:
    """
    Gerencia a execução em massa de arquivos INP.
    """

    def __init__(self, base_dir: str, abaqus_path: str = None):
        self.base_dir = Path(base_dir).resolve()
        self.abaqus_path = abaqus_path or r"C:\SIMULIA\Commands\abq2021.bat"

        # Logs
        self.log_dir = self.base_dir / "simulation_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logger()

        self.results = []

    def _setup_logger(self):
        self.logger = logging.getLogger("INPRunner")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            ch = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def find_inp_files(self, pattern: str = "**/*_FI.inp") -> List[Path]:
        files = list(self.base_dir.glob(pattern))
        files.sort()
        self.logger.info(f"Encontrados {len(files)} arquivos com padrão '{pattern}'.")
        return files

    def run_all(self, n_cpus=4, silent=True):
        """
        Roda todas as simulações.
        silent=True: Ideal para Batch (não suja tela).
        silent=False: Ideal para Debug (vê erros ao vivo).
        """
        inp_files = self.find_inp_files()
        if not inp_files:
            self.logger.warning("Nenhum arquivo encontrado.")
            return

        self.logger.info(f"Iniciando lote de {len(inp_files)} simulações...")

        success_count = 0
        total = len(inp_files)

        for i, inp_path in enumerate(inp_files, 1):
            self.logger.info(f"\n--- SIMULAÇÃO {i}/{total}: {inp_path.name} ---")

            config = AbaqusJobConfig(
                job_name=inp_path.stem,
                input_file=str(inp_path),
                output_dir=str(inp_path.parent),
                abaqus_cmd=self.abaqus_path,
                n_cpus=n_cpus,
                silent_mode=silent,  # Configurável
                auto_cleanup=True  # Limpa lixo automaticamente
            )

            runner = AbaqusJobRunner(config)

            self.logger.info(f"Submetendo Job (Scratch: {runner.scratch_dir})...")
            code, duration, err = runner.run()

            # Validação
            odb_path = inp_path.parent / f"{inp_path.stem}.odb"
            is_success = (code == 0) and odb_path.exists()

            if is_success:
                self.logger.info(f"✓ Sucesso ({duration:.1f}s)")
                success_count += 1
            else:
                self.logger.error(f"✗ Falha ({duration:.1f}s). Código: {code}")
                if err: self.logger.error(f"Erro: {err[:300]}...")  # Mostra os primeiros 300 chars do erro

            self.results.append({
                'file': inp_path.name,
                'success': is_success,
                'time': duration,
                'error': err if not is_success else ""
            })

        self._generate_report(total, success_count)

    def _generate_report(self, total, success):
        report_path = self.log_dir / "summary_report.txt"
        try:
            with open(report_path, "w") as f:
                f.write(f"Resumo da Execução\n{'=' * 20}\n")
                f.write(f"Total: {total}\nSucessos: {success}\nFalhas: {total - success}\n\n")
                for r in self.results:
                    status = "OK" if r['success'] else "ERRO"
                    f.write(f"{r['file']:<40} | {status} | {r['time']:.1f}s")
                    if r['error']:
                        f.write(f" | Erro: {r['error'][:50]}...")
                    f.write("\n")
            self.logger.info(f"\nRelatório salvo em: {report_path}")
        except Exception:
            pass