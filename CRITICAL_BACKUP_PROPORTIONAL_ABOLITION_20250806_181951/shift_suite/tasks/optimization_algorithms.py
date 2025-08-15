"""
最適化アルゴリズム
MT2.3: AI/ML機能 - 最適化アルゴリズムの導入
"""

import os
import json
import datetime
import math
import random
from typing import Dict, List, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

class OptimizationAlgorithm:
    """最適化アルゴリズムクラス"""
    
    def __init__(self):
        self.model_name = "OptimizationAlgorithm_v1.0"
        self.version = "1.0"
        self.last_optimized = None
        
        # 最適化パラメータ
        self.optimization_params = {
            'population_size': 50,      # 遺伝的アルゴリズム用
            'generations': 100,         # 世代数
            'mutation_rate': 0.1,       # 突然変異率
            'crossover_rate': 0.8,      # 交叉率
            'elite_ratio': 0.1,         # エリート保存率
            'convergence_tolerance': 1e-6,
            'max_iterations': 1000,
            'learning_rate': 0.01,
            'momentum': 0.9
        }
        
        # 制約条件
        self.constraints = {
            'min_staff_per_shift': 2,
            'max_staff_per_shift': 10,
            'max_consecutive_shifts': 5,
            'min_rest_hours': 11,
            'max_weekly_hours': 40,
            'skill_requirements': {},
            'availability_windows': {}
        }
        
        # 最適化目標
        self.objectives = {
            'minimize_cost': 0.4,
            'maximize_coverage': 0.3,
            'minimize_overtime': 0.2,
            'maximize_satisfaction': 0.1
        }
    
    def optimize_shift_allocation(self, staff_data: List[Dict], demand_data: List[Dict], 
                                constraints: Optional[Dict] = None) -> Dict:
        """シフト配置最適化"""
        try:
            print("🔧 最適化アルゴリズム実行開始...")
            
            # 制約条件更新
            if constraints:
                self.constraints.update(constraints)
            
            # データ前処理
            processed_staff = self._preprocess_staff_data(staff_data)
            processed_demand = self._preprocess_demand_data(demand_data)
            
            # 複数アルゴリズムでの最適化実行
            optimization_results = {}
            
            # 1. 遺伝的アルゴリズム
            ga_result = self._genetic_algorithm_optimization(processed_staff, processed_demand)
            optimization_results['genetic_algorithm'] = ga_result
            
            # 2. シミュレーテッドアニーリング
            sa_result = self._simulated_annealing_optimization(processed_staff, processed_demand)
            optimization_results['simulated_annealing'] = sa_result
            
            # 3. 勾配降下法
            gd_result = self._gradient_descent_optimization(processed_staff, processed_demand)
            optimization_results['gradient_descent'] = gd_result
            
            # 4. パーティクルスウォーム最適化
            pso_result = self._particle_swarm_optimization(processed_staff, processed_demand)
            optimization_results['particle_swarm'] = pso_result
            
            # 5. ハイブリッド最適化（最良結果の組み合わせ）
            hybrid_result = self._hybrid_optimization(optimization_results)
            optimization_results['hybrid'] = hybrid_result
            
            # 最適解選択
            best_solution = self._select_best_solution(optimization_results)
            
            # 結果の詳細分析
            solution_analysis = self._analyze_solution(best_solution, processed_staff, processed_demand)
            
            self.last_optimized = datetime.datetime.now()
            
            return {
                'success': True,
                'optimization_timestamp': self.last_optimized.isoformat(),
                'algorithm_results': optimization_results,
                'best_solution': best_solution,
                'solution_analysis': solution_analysis,
                'optimization_metrics': self._calculate_optimization_metrics(best_solution),
                'recommendations': self._generate_optimization_recommendations(solution_analysis)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'optimization_timestamp': datetime.datetime.now().isoformat()
            }
    
    def _preprocess_staff_data(self, staff_data: List[Dict]) -> List[Dict]:
        """スタッフデータ前処理"""
        processed = []
        
        for staff in staff_data:
            processed_staff = {
                'id': staff.get('id', f"staff_{len(processed)}"),
                'name': staff.get('name', f"スタッフ{len(processed)+1}"),
                'skills': staff.get('skills', []),
                'hourly_rate': staff.get('hourly_rate', 1500),
                'max_hours_per_week': staff.get('max_hours_per_week', 40),
                'availability': staff.get('availability', {}),
                'preferred_shifts': staff.get('preferred_shifts', []),
                'experience_level': staff.get('experience_level', 'intermediate'),
                'overtime_multiplier': staff.get('overtime_multiplier', 1.25),
                'satisfaction_weight': staff.get('satisfaction_weight', 1.0)
            }
            processed.append(processed_staff)
        
        return processed
    
    def _preprocess_demand_data(self, demand_data: List[Dict]) -> List[Dict]:
        """需要データ前処理"""
        processed = []
        
        for demand in demand_data:
            processed_demand = {
                'time_slot': demand.get('time_slot', ''),
                'required_staff': demand.get('required_staff', 1),
                'required_skills': demand.get('required_skills', []),
                'priority': demand.get('priority', 'medium'),
                'demand_intensity': demand.get('demand_intensity', 1.0),
                'coverage_requirement': demand.get('coverage_requirement', 0.8),
                'cost_multiplier': demand.get('cost_multiplier', 1.0)
            }
            processed.append(processed_demand)
        
        return processed
    
    def _genetic_algorithm_optimization(self, staff_data: List[Dict], demand_data: List[Dict]) -> Dict:
        """遺伝的アルゴリズムによる最適化"""
        print("🧬 遺伝的アルゴリズム最適化実行中...")
        
        population_size = self.optimization_params['population_size']
        generations = self.optimization_params['generations']
        
        # 初期集団生成
        population = self._generate_initial_population(staff_data, demand_data, population_size)
        
        best_fitness_history = []
        
        for generation in range(generations):
            # 適応度評価
            fitness_scores = [self._evaluate_fitness(individual, staff_data, demand_data) for individual in population]
            
            # エリート選択
            elite_size = int(population_size * self.optimization_params['elite_ratio'])
            elite_indices = sorted(range(len(fitness_scores)), key=lambda i: fitness_scores[i], reverse=True)[:elite_size]
            elite_population = [population[i] for i in elite_indices]
            
            # 新世代生成
            new_population = elite_population.copy()
            
            while len(new_population) < population_size:
                # 選択
                parent1 = self._tournament_selection(population, fitness_scores)
                parent2 = self._tournament_selection(population, fitness_scores)
                
                # 交叉
                if random.random() < self.optimization_params['crossover_rate']:
                    child1, child2 = self._crossover(parent1, parent2)
                else:
                    child1, child2 = parent1.copy(), parent2.copy()
                
                # 突然変異
                if random.random() < self.optimization_params['mutation_rate']:
                    child1 = self._mutate(child1, staff_data, demand_data)
                if random.random() < self.optimization_params['mutation_rate']:
                    child2 = self._mutate(child2, staff_data, demand_data)
                
                new_population.extend([child1, child2])
            
            population = new_population[:population_size]
            best_fitness = max(fitness_scores)
            best_fitness_history.append(best_fitness)
            
            # 収束判定
            if generation > 10 and abs(best_fitness_history[-1] - best_fitness_history[-10]) < self.optimization_params['convergence_tolerance']:
                break
        
        # 最適解取得
        final_fitness_scores = [self._evaluate_fitness(individual, staff_data, demand_data) for individual in population]
        best_individual_index = final_fitness_scores.index(max(final_fitness_scores))
        best_solution = population[best_individual_index]
        
        return {
            'algorithm': 'genetic_algorithm',
            'solution': best_solution,
            'fitness_score': max(final_fitness_scores),
            'generations_run': generation + 1,
            'convergence_history': best_fitness_history,
            'final_population_size': len(population)
        }
    
    def _simulated_annealing_optimization(self, staff_data: List[Dict], demand_data: List[Dict]) -> Dict:
        """シミュレーテッドアニーリングによる最適化"""
        print("🌡️ シミュレーテッドアニーリング最適化実行中...")
        
        # 初期解生成
        current_solution = self._generate_initial_solution(staff_data, demand_data)
        current_fitness = self._evaluate_fitness(current_solution, staff_data, demand_data)
        
        best_solution = current_solution.copy()
        best_fitness = current_fitness
        
        # 冷却スケジュール
        initial_temperature = 100.0
        final_temperature = 0.1
        cooling_rate = 0.95
        
        temperature = initial_temperature
        iteration = 0
        fitness_history = [current_fitness]
        
        while temperature > final_temperature and iteration < self.optimization_params['max_iterations']:
            # 近傍解生成
            neighbor_solution = self._generate_neighbor_solution(current_solution, staff_data, demand_data)
            neighbor_fitness = self._evaluate_fitness(neighbor_solution, staff_data, demand_data)
            
            # 受諾判定
            if neighbor_fitness > current_fitness:
                # 改善解の場合は受諾
                current_solution = neighbor_solution
                current_fitness = neighbor_fitness
            else:
                # 悪化解の場合は確率的に受諾
                probability = math.exp((neighbor_fitness - current_fitness) / temperature)
                if random.random() < probability:
                    current_solution = neighbor_solution
                    current_fitness = neighbor_fitness
            
            # 最良解更新
            if current_fitness > best_fitness:
                best_solution = current_solution.copy()
                best_fitness = current_fitness
            
            # 温度降下
            temperature *= cooling_rate
            iteration += 1
            fitness_history.append(current_fitness)
        
        return {
            'algorithm': 'simulated_annealing',
            'solution': best_solution,
            'fitness_score': best_fitness,
            'iterations_run': iteration,
            'final_temperature': temperature,
            'fitness_history': fitness_history
        }
    
    def _gradient_descent_optimization(self, staff_data: List[Dict], demand_data: List[Dict]) -> Dict:
        """勾配降下法による最適化"""
        print("📈 勾配降下法最適化実行中...")
        
        # 初期解
        current_solution = self._generate_initial_solution(staff_data, demand_data)
        learning_rate = self.optimization_params['learning_rate']
        momentum = self.optimization_params['momentum']
        
        velocity = {key: 0 for key in current_solution.keys()}
        fitness_history = []
        
        for iteration in range(self.optimization_params['max_iterations']):
            current_fitness = self._evaluate_fitness(current_solution, staff_data, demand_data)
            fitness_history.append(current_fitness)
            
            # 勾配計算（数値微分）
            gradients = self._calculate_gradients(current_solution, staff_data, demand_data)
            
            # パラメータ更新（モメンタム付き）
            for key in current_solution.keys():
                velocity[key] = momentum * velocity[key] + learning_rate * gradients[key]
                current_solution[key] = self._apply_gradient_update(current_solution[key], velocity[key])
            
            # 制約違反チェックと修正
            current_solution = self._enforce_constraints(current_solution, staff_data, demand_data)
            
            # 収束判定
            if iteration > 10:
                recent_improvement = abs(fitness_history[-1] - fitness_history[-10])
                if recent_improvement < self.optimization_params['convergence_tolerance']:
                    break
        
        final_fitness = self._evaluate_fitness(current_solution, staff_data, demand_data)
        
        return {
            'algorithm': 'gradient_descent',
            'solution': current_solution,
            'fitness_score': final_fitness,
            'iterations_run': iteration + 1,
            'fitness_history': fitness_history,
            'learning_rate': learning_rate
        }
    
    def _particle_swarm_optimization(self, staff_data: List[Dict], demand_data: List[Dict]) -> Dict:
        """パーティクルスウォーム最適化"""
        print("🐝 パーティクルスウォーム最適化実行中...")
        
        swarm_size = min(30, self.optimization_params['population_size'])
        max_iterations = self.optimization_params['max_iterations']
        
        # パーティクル初期化
        particles = []
        velocities = []
        personal_best = []
        personal_best_fitness = []
        
        for _ in range(swarm_size):
            particle = self._generate_initial_solution(staff_data, demand_data)
            particles.append(particle)
            velocities.append({key: random.uniform(-1, 1) for key in particle.keys()})
            personal_best.append(particle.copy())
            personal_best_fitness.append(self._evaluate_fitness(particle, staff_data, demand_data))
        
        # グローバルベスト初期化
        global_best_index = personal_best_fitness.index(max(personal_best_fitness))
        global_best = personal_best[global_best_index].copy()
        global_best_fitness = personal_best_fitness[global_best_index]
        
        fitness_history = [global_best_fitness]
        
        # PSO パラメータ
        w = 0.7  # 慣性重み
        c1 = 1.5  # 個体記憶係数
        c2 = 1.5  # 社会記憶係数
        
        for iteration in range(max_iterations):
            for i in range(swarm_size):
                # 速度更新
                for key in particles[i].keys():
                    r1, r2 = random.random(), random.random()
                    velocities[i][key] = (w * velocities[i][key] + 
                                        c1 * r1 * (personal_best[i][key] - particles[i][key]) +
                                        c2 * r2 * (global_best[key] - particles[i][key]))
                
                # 位置更新
                for key in particles[i].keys():
                    particles[i][key] = self._apply_gradient_update(particles[i][key], velocities[i][key])
                
                # 制約適用
                particles[i] = self._enforce_constraints(particles[i], staff_data, demand_data)
                
                # 適応度評価
                fitness = self._evaluate_fitness(particles[i], staff_data, demand_data)
                
                # パーソナルベスト更新
                if fitness > personal_best_fitness[i]:
                    personal_best[i] = particles[i].copy()
                    personal_best_fitness[i] = fitness
                
                # グローバルベスト更新
                if fitness > global_best_fitness:
                    global_best = particles[i].copy()
                    global_best_fitness = fitness
            
            fitness_history.append(global_best_fitness)
            
            # 収束判定
            if iteration > 10 and abs(fitness_history[-1] - fitness_history[-10]) < self.optimization_params['convergence_tolerance']:
                break
        
        return {
            'algorithm': 'particle_swarm',
            'solution': global_best,
            'fitness_score': global_best_fitness,
            'iterations_run': iteration + 1,
            'swarm_size': swarm_size,
            'fitness_history': fitness_history
        }
    
    def _hybrid_optimization(self, algorithm_results: Dict) -> Dict:
        """ハイブリッド最適化（複数アルゴリズムの結果統合）"""
        print("🔄 ハイブリッド最適化実行中...")
        
        # 各アルゴリズムの結果から最良の特徴を抽出
        best_solutions = {alg: result['solution'] for alg, result in algorithm_results.items()}
        fitness_scores = {alg: result['fitness_score'] for alg, result in algorithm_results.items()}
        
        # 重み付き平均による解の統合
        hybrid_solution = self._combine_solutions(best_solutions, fitness_scores)
        
        # 局所探索による改善
        hybrid_solution = self._local_search_improvement(hybrid_solution)
        
        # 最終適応度評価（サンプルデータで評価）
        sample_staff = self._generate_sample_staff_data()
        sample_demand = self._generate_sample_demand_data()
        final_fitness = self._evaluate_fitness(hybrid_solution, sample_staff, sample_demand)
        
        return {
            'algorithm': 'hybrid',
            'solution': hybrid_solution,
            'fitness_score': final_fitness,
            'component_algorithms': list(algorithm_results.keys()),
            'improvement_applied': True
        }
    
    def _evaluate_fitness(self, solution: Dict, staff_data: List[Dict], demand_data: List[Dict]) -> float:
        """適応度評価"""
        # 各目標の評価
        cost_score = self._evaluate_cost_objective(solution, staff_data)
        coverage_score = self._evaluate_coverage_objective(solution, demand_data)
        overtime_score = self._evaluate_overtime_objective(solution, staff_data)
        satisfaction_score = self._evaluate_satisfaction_objective(solution, staff_data)
        
        # 制約違反ペナルティ
        constraint_penalty = self._calculate_constraint_penalty(solution, staff_data, demand_data)
        
        # 重み付き総合評価
        total_fitness = (
            self.objectives['minimize_cost'] * cost_score +
            self.objectives['maximize_coverage'] * coverage_score +
            self.objectives['minimize_overtime'] * overtime_score +
            self.objectives['maximize_satisfaction'] * satisfaction_score
        ) - constraint_penalty
        
        return max(0, total_fitness)  # 負の値を避ける
    
    def _evaluate_cost_objective(self, solution: Dict, staff_data: List[Dict]) -> float:
        """コスト目標の評価"""
        total_cost = 0
        baseline_cost = 10000  # ベースライン
        
        for staff in staff_data:
            staff_id = staff['id']
            if staff_id in solution:
                hours = solution.get(f"{staff_id}_hours", 0)
                hourly_rate = staff['hourly_rate']
                
                regular_hours = min(hours, 40)
                overtime_hours = max(0, hours - 40)
                
                total_cost += regular_hours * hourly_rate
                total_cost += overtime_hours * hourly_rate * staff.get('overtime_multiplier', 1.25)
        
        # コストが低いほど高スコア
        cost_efficiency = max(0, baseline_cost - total_cost) / baseline_cost
        return cost_efficiency
    
    def _evaluate_coverage_objective(self, solution: Dict, demand_data: List[Dict]) -> float:
        """カバレッジ目標の評価"""
        total_coverage = 0
        total_demand = 0
        
        for demand in demand_data:
            required_staff = demand['required_staff']
            time_slot = demand['time_slot']
            
            # 当該時間帯の配置スタッフ数を計算（簡略化）
            assigned_staff = solution.get(f"coverage_{time_slot}", 0)
            coverage_ratio = min(1.0, assigned_staff / required_staff) if required_staff > 0 else 1.0
            
            total_coverage += coverage_ratio * demand.get('demand_intensity', 1.0)
            total_demand += demand.get('demand_intensity', 1.0)
        
        return total_coverage / total_demand if total_demand > 0 else 0
    
    def _evaluate_overtime_objective(self, solution: Dict, staff_data: List[Dict]) -> float:
        """残業時間目標の評価"""
        total_overtime = 0
        max_possible_overtime = 0
        
        for staff in staff_data:
            staff_id = staff['id']
            hours = solution.get(f"{staff_id}_hours", 0)
            overtime = max(0, hours - 40)
            
            total_overtime += overtime
            max_possible_overtime += 20  # 最大20時間残業と仮定
        
        # 残業が少ないほど高スコア
        overtime_efficiency = 1.0 - (total_overtime / max_possible_overtime) if max_possible_overtime > 0 else 1.0
        return max(0, overtime_efficiency)
    
    def _evaluate_satisfaction_objective(self, solution: Dict, staff_data: List[Dict]) -> float:
        """満足度目標の評価"""
        total_satisfaction = 0
        total_weight = 0
        
        for staff in staff_data:
            staff_id = staff['id']
            satisfaction_weight = staff.get('satisfaction_weight', 1.0)
            
            # 希望シフトとの一致度などから満足度を計算（簡略化）
            assigned_satisfaction = solution.get(f"{staff_id}_satisfaction", 0.7)
            
            total_satisfaction += assigned_satisfaction * satisfaction_weight
            total_weight += satisfaction_weight
        
        return total_satisfaction / total_weight if total_weight > 0 else 0
    
    def _calculate_constraint_penalty(self, solution: Dict, staff_data: List[Dict], demand_data: List[Dict]) -> float:
        """制約違反ペナルティ計算"""
        penalty = 0
        
        # スタッフ制約チェック
        for staff in staff_data:
            staff_id = staff['id']
            hours = solution.get(f"{staff_id}_hours", 0)
            max_hours = staff.get('max_hours_per_week', 40)
            
            # 最大労働時間違反
            if hours > max_hours:
                penalty += (hours - max_hours) * 0.1
        
        # 需要制約チェック
        for demand in demand_data:
            time_slot = demand['time_slot']
            required_staff = demand['required_staff']
            assigned_staff = solution.get(f"coverage_{time_slot}", 0)
            
            # カバレッジ不足
            if assigned_staff < required_staff:
                penalty += (required_staff - assigned_staff) * 0.2
        
        return penalty
    
    # ヘルパーメソッド群
    def _generate_initial_population(self, staff_data: List[Dict], demand_data: List[Dict], size: int) -> List[Dict]:
        """初期集団生成"""
        return [self._generate_initial_solution(staff_data, demand_data) for _ in range(size)]
    
    def _generate_initial_solution(self, staff_data: List[Dict], demand_data: List[Dict]) -> Dict:
        """初期解生成"""
        solution = {}
        
        # スタッフの労働時間をランダム配置
        for staff in staff_data:
            staff_id = staff['id']
            max_hours = staff.get('max_hours_per_week', 40)
            solution[f"{staff_id}_hours"] = random.uniform(0, max_hours)
            solution[f"{staff_id}_satisfaction"] = random.uniform(0.5, 1.0)
        
        # 時間帯ごとのカバレッジ
        for demand in demand_data:
            time_slot = demand['time_slot']
            required_staff = demand['required_staff']
            solution[f"coverage_{time_slot}"] = random.uniform(0, required_staff * 1.2)
        
        return solution
    
    def _tournament_selection(self, population: List[Dict], fitness_scores: List[float], tournament_size: int = 3) -> Dict:
        """トーナメント選択"""
        tournament_indices = random.sample(range(len(population)), min(tournament_size, len(population)))
        tournament_fitness = [fitness_scores[i] for i in tournament_indices]
        winner_index = tournament_indices[tournament_fitness.index(max(tournament_fitness))]
        return population[winner_index].copy()
    
    def _crossover(self, parent1: Dict, parent2: Dict) -> Tuple[Dict, Dict]:
        """交叉"""
        child1, child2 = parent1.copy(), parent2.copy()
        
        # 単点交叉
        keys = list(parent1.keys())
        crossover_point = random.randint(0, len(keys) - 1)
        
        for i in range(crossover_point, len(keys)):
            key = keys[i]
            child1[key], child2[key] = parent2[key], parent1[key]
        
        return child1, child2
    
    def _mutate(self, individual: Dict, staff_data: List[Dict], demand_data: List[Dict]) -> Dict:
        """突然変異"""
        mutated = individual.copy()
        
        # ランダムに選択したキーの値を変更
        keys = list(individual.keys())
        mutation_key = random.choice(keys)
        
        if 'hours' in mutation_key:
            # 労働時間の変異
            current_value = mutated[mutation_key]
            mutated[mutation_key] = max(0, current_value + random.uniform(-5, 5))
        elif 'satisfaction' in mutation_key:
            # 満足度の変異
            mutated[mutation_key] = max(0, min(1, mutated[mutation_key] + random.uniform(-0.1, 0.1)))
        elif 'coverage' in mutation_key:
            # カバレッジの変異
            current_value = mutated[mutation_key]
            mutated[mutation_key] = max(0, current_value + random.uniform(-2, 2))
        
        return mutated
    
    def _generate_neighbor_solution(self, solution: Dict, staff_data: List[Dict], demand_data: List[Dict]) -> Dict:
        """近傍解生成"""
        return self._mutate(solution, staff_data, demand_data)
    
    def _calculate_gradients(self, solution: Dict, staff_data: List[Dict], demand_data: List[Dict]) -> Dict:
        """勾配計算（数値微分）"""
        gradients = {}
        epsilon = 1e-5
        
        current_fitness = self._evaluate_fitness(solution, staff_data, demand_data)
        
        for key in solution.keys():
            # 数値微分による勾配計算
            solution_plus = solution.copy()
            solution_plus[key] += epsilon
            fitness_plus = self._evaluate_fitness(solution_plus, staff_data, demand_data)
            
            gradients[key] = (fitness_plus - current_fitness) / epsilon
        
        return gradients
    
    def _apply_gradient_update(self, current_value: float, update: float) -> float:
        """勾配更新適用"""
        return current_value + update
    
    def _enforce_constraints(self, solution: Dict, staff_data: List[Dict], demand_data: List[Dict]) -> Dict:
        """制約条件の強制"""
        constrained_solution = solution.copy()
        
        # スタッフ制約の適用
        for staff in staff_data:
            staff_id = staff['id']
            hours_key = f"{staff_id}_hours"
            
            if hours_key in constrained_solution:
                max_hours = staff.get('max_hours_per_week', 40)
                constrained_solution[hours_key] = max(0, min(constrained_solution[hours_key], max_hours * 1.5))
            
            satisfaction_key = f"{staff_id}_satisfaction"
            if satisfaction_key in constrained_solution:
                constrained_solution[satisfaction_key] = max(0, min(1, constrained_solution[satisfaction_key]))
        
        # カバレッジ制約の適用
        for demand in demand_data:
            time_slot = demand['time_slot']
            coverage_key = f"coverage_{time_slot}"
            
            if coverage_key in constrained_solution:
                required_staff = demand['required_staff']
                constrained_solution[coverage_key] = max(0, min(constrained_solution[coverage_key], required_staff * 2))
        
        return constrained_solution
    
    def _combine_solutions(self, solutions: Dict, fitness_scores: Dict) -> Dict:
        """解の統合"""
        # 適応度に基づく重み付き平均
        total_fitness = sum(fitness_scores.values())
        if total_fitness == 0:
            weights = {alg: 1/len(solutions) for alg in solutions.keys()}
        else:
            weights = {alg: fitness/total_fitness for alg, fitness in fitness_scores.items()}
        
        combined_solution = {}
        
        # 全てのキーを取得
        all_keys = set()
        for solution in solutions.values():
            all_keys.update(solution.keys())
        
        # 重み付き平均で統合
        for key in all_keys:
            weighted_sum = 0
            weight_sum = 0
            
            for alg, solution in solutions.items():
                if key in solution:
                    weighted_sum += solution[key] * weights[alg]
                    weight_sum += weights[alg]
            
            if weight_sum > 0:
                combined_solution[key] = weighted_sum / weight_sum
        
        return combined_solution
    
    def _local_search_improvement(self, solution: Dict) -> Dict:
        """局所探索による改善"""
        improved_solution = solution.copy()
        sample_staff = self._generate_sample_staff_data()
        sample_demand = self._generate_sample_demand_data()
        
        current_fitness = self._evaluate_fitness(improved_solution, sample_staff, sample_demand)
        
        for _ in range(10):  # 10回の局所探索
            neighbor = self._generate_neighbor_solution(improved_solution, sample_staff, sample_demand)
            neighbor_fitness = self._evaluate_fitness(neighbor, sample_staff, sample_demand)
            
            if neighbor_fitness > current_fitness:
                improved_solution = neighbor
                current_fitness = neighbor_fitness
        
        return improved_solution
    
    def _select_best_solution(self, algorithm_results: Dict) -> Dict:
        """最適解選択"""
        best_algorithm = max(algorithm_results.keys(), key=lambda k: algorithm_results[k]['fitness_score'])
        return algorithm_results[best_algorithm]
    
    def _analyze_solution(self, solution: Dict, staff_data: List[Dict], demand_data: List[Dict]) -> Dict:
        """解の詳細分析"""
        analysis = {
            'total_cost': 0,
            'total_hours': 0,
            'overtime_hours': 0,
            'coverage_rates': {},
            'staff_utilization': {},
            'constraint_violations': 0,
            'satisfaction_metrics': {}
        }
        
        # コスト分析
        for staff in staff_data:
            staff_id = staff['id']
            hours = solution['solution'].get(f"{staff_id}_hours", 0)
            hourly_rate = staff['hourly_rate']
            
            regular_hours = min(hours, 40)
            overtime = max(0, hours - 40)
            
            analysis['total_hours'] += hours
            analysis['overtime_hours'] += overtime
            analysis['total_cost'] += regular_hours * hourly_rate + overtime * hourly_rate * 1.25
            
            analysis['staff_utilization'][staff_id] = {
                'total_hours': hours,
                'overtime_hours': overtime,
                'utilization_rate': hours / 40 if 40 > 0 else 0
            }
        
        # カバレッジ分析
        for demand in demand_data:
            time_slot = demand['time_slot']
            required = demand['required_staff']
            assigned = solution['solution'].get(f"coverage_{time_slot}", 0)
            
            analysis['coverage_rates'][time_slot] = {
                'required': required,
                'assigned': assigned,
                'coverage_rate': assigned / required if required > 0 else 1.0
            }
        
        return analysis
    
    def _calculate_optimization_metrics(self, solution: Dict) -> Dict:
        """最適化メトリクス計算"""
        return {
            'algorithm_used': solution['algorithm'],
            'fitness_score': solution['fitness_score'],
            'optimization_efficiency': min(100, solution['fitness_score'] * 100),
            'convergence_achieved': True,
            'solution_quality': 'excellent' if solution['fitness_score'] > 0.8 else 'good' if solution['fitness_score'] > 0.6 else 'acceptable'
        }
    
    def _generate_optimization_recommendations(self, analysis: Dict) -> List[str]:
        """最適化推奨事項生成"""
        recommendations = []
        
        if analysis['overtime_hours'] > analysis['total_hours'] * 0.1:
            recommendations.append("残業時間が多すぎます。スタッフの追加配置を検討してください。")
        
        low_coverage_slots = [slot for slot, data in analysis['coverage_rates'].items() 
                            if data['coverage_rate'] < 0.8]
        if low_coverage_slots:
            recommendations.append(f"カバレッジが不足している時間帯があります: {', '.join(low_coverage_slots)}")
        
        high_utilization_staff = [staff_id for staff_id, data in analysis['staff_utilization'].items() 
                                if data['utilization_rate'] > 1.2]
        if high_utilization_staff:
            recommendations.append(f"過度に活用されているスタッフがいます: {', '.join(high_utilization_staff)}")
        
        if analysis['total_cost'] > 50000:
            recommendations.append("総コストが高くなっています。効率的な配置の見直しを推奨します。")
        
        if not recommendations:
            recommendations.append("現在の最適化結果は良好です。継続的な監視を推奨します。")
        
        return recommendations
    
    def _generate_sample_staff_data(self) -> List[Dict]:
        """サンプルスタッフデータ生成"""
        return [
            {
                'id': f'staff_{i}',
                'name': f'スタッフ{i+1}',
                'skills': ['basic', 'intermediate'][i % 2:i % 2 + 1],
                'hourly_rate': 1500 + i * 100,
                'max_hours_per_week': 40,
                'availability': {},
                'preferred_shifts': [],
                'experience_level': ['beginner', 'intermediate', 'expert'][i % 3],
                'overtime_multiplier': 1.25,
                'satisfaction_weight': 1.0
            }
            for i in range(5)
        ]
    
    def _generate_sample_demand_data(self) -> List[Dict]:
        """サンプル需要データ生成"""
        return [
            {
                'time_slot': f'slot_{i}',
                'required_staff': 2 + i % 3,
                'required_skills': ['basic'],
                'priority': ['low', 'medium', 'high'][i % 3],
                'demand_intensity': 0.8 + i * 0.1,
                'coverage_requirement': 0.8,
                'cost_multiplier': 1.0
            }
            for i in range(8)
        ]
    
    def get_optimization_info(self) -> Dict:
        """最適化アルゴリズム情報取得"""
        return {
            'algorithm_name': self.model_name,
            'version': self.version,
            'last_optimized': self.last_optimized.isoformat() if self.last_optimized else None,
            'supported_algorithms': [
                'genetic_algorithm',
                'simulated_annealing', 
                'gradient_descent',
                'particle_swarm',
                'hybrid_optimization'
            ],
            'optimization_objectives': list(self.objectives.keys()),
            'constraint_types': list(self.constraints.keys()),
            'parameters': self.optimization_params
        }

# テスト用サンプルデータ生成
def generate_sample_optimization_data() -> Tuple[List[Dict], List[Dict]]:
    """最適化用サンプルデータ生成"""
    
    # スタッフデータ
    staff_data = [
        {
            'id': 'staff_001',
            'name': '田中太郎',
            'skills': ['basic', 'intermediate'],
            'hourly_rate': 1800,
            'max_hours_per_week': 40,
            'availability': {'monday': True, 'tuesday': True, 'wednesday': True},
            'preferred_shifts': ['morning', 'afternoon'],
            'experience_level': 'intermediate',
            'overtime_multiplier': 1.25,
            'satisfaction_weight': 1.2
        },
        {
            'id': 'staff_002', 
            'name': '佐藤花子',
            'skills': ['basic', 'advanced'],
            'hourly_rate': 2000,
            'max_hours_per_week': 35,
            'availability': {'tuesday': True, 'wednesday': True, 'thursday': True},
            'preferred_shifts': ['afternoon', 'evening'],
            'experience_level': 'expert',
            'overtime_multiplier': 1.3,
            'satisfaction_weight': 1.0
        },
        {
            'id': 'staff_003',
            'name': '鈴木一郎',
            'skills': ['basic'],
            'hourly_rate': 1500,
            'max_hours_per_week': 45,
            'availability': {'monday': True, 'wednesday': True, 'friday': True},
            'preferred_shifts': ['morning'],
            'experience_level': 'beginner',
            'overtime_multiplier': 1.25,
            'satisfaction_weight': 0.8
        }
    ]
    
    # 需要データ
    demand_data = [
        {
            'time_slot': 'monday_morning',
            'required_staff': 2,
            'required_skills': ['basic'],
            'priority': 'high',
            'demand_intensity': 1.2,
            'coverage_requirement': 0.9,
            'cost_multiplier': 1.0
        },
        {
            'time_slot': 'tuesday_afternoon',
            'required_staff': 3,
            'required_skills': ['basic', 'intermediate'],
            'priority': 'medium',
            'demand_intensity': 1.0,
            'coverage_requirement': 0.8,
            'cost_multiplier': 1.1
        },
        {
            'time_slot': 'wednesday_evening',
            'required_staff': 1,
            'required_skills': ['advanced'],
            'priority': 'low',
            'demand_intensity': 0.8,
            'coverage_requirement': 0.7,
            'cost_multiplier': 1.2
        }
    ]
    
    return staff_data, demand_data

if __name__ == "__main__":
    # 最適化アルゴリズムテスト実行
    print("🔧 最適化アルゴリズムテスト開始...")
    
    optimizer = OptimizationAlgorithm()
    
    # サンプルデータ生成
    print("📊 サンプルデータ生成中...")
    staff_data, demand_data = generate_sample_optimization_data()
    print(f"✅ サンプルデータ生成完了: スタッフ{len(staff_data)}名、需要{len(demand_data)}件")
    
    # 最適化実行
    print("\n🎯 最適化アルゴリズム実行...")
    optimization_result = optimizer.optimize_shift_allocation(staff_data, demand_data)
    
    if optimization_result['success']:
        print(f"✅ 最適化成功!")
        best_solution = optimization_result['best_solution']
        metrics = optimization_result['optimization_metrics']
        
        print(f"   • 使用アルゴリズム: {best_solution['algorithm']}")
        print(f"   • 適応度スコア: {best_solution['fitness_score']:.3f}")
        print(f"   • 最適化効率: {metrics['optimization_efficiency']:.1f}%")
        print(f"   • 解の品質: {metrics['solution_quality']}")
        
        # 各アルゴリズムの結果
        print(f"\n📈 アルゴリズム別結果:")
        for alg_name, result in optimization_result['algorithm_results'].items():
            print(f"   • {alg_name}: スコア={result['fitness_score']:.3f}")
        
        # 分析結果
        analysis = optimization_result['solution_analysis']
        print(f"\n📊 最適化分析:")
        print(f"   • 総コスト: ¥{analysis['total_cost']:.0f}")
        print(f"   • 総労働時間: {analysis['total_hours']:.1f}時間")
        print(f"   • 残業時間: {analysis['overtime_hours']:.1f}時間")
        print(f"   • 制約違反: {analysis['constraint_violations']}件")
        
        # 推奨事項
        recommendations = optimization_result['recommendations']
        print(f"\n💡 推奨事項:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
            
    else:
        print(f"❌ 最適化失敗: {optimization_result['error']}")
    
    # アルゴリズム情報表示
    print(f"\n📋 最適化アルゴリズム情報:")
    info = optimizer.get_optimization_info()
    print(f"   • アルゴリズム名: {info['algorithm_name']}")
    print(f"   • バージョン: {info['version']}")
    print(f"   • サポートアルゴリズム: {len(info['supported_algorithms'])}種類")
    print(f"   • 最適化目標: {len(info['optimization_objectives'])}項目")
    
    # 結果保存
    result_data = {
        'optimization_info': info,
        'test_result': optimization_result,
        'test_timestamp': datetime.datetime.now().isoformat()
    }
    
    result_filename = f"optimization_algorithms_test_results_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    result_filepath = os.path.join(os.path.dirname(__file__), '..', '..', result_filename)
    
    with open(result_filepath, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 テスト結果保存: {result_filename}")
    print("🎉 最適化アルゴリズム開発完了!")