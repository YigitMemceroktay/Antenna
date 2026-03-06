$begin 'Profile'
	$begin 'ProfileGroup'
		MajorVer=2024
		MinorVer=2
		Name='Solution Process'
		$begin 'StartInfo'
			I(1, 'Start Time', '02/28/2026 15:10:02')
			I(1, 'Host', 'SIMPL-DZ11-2')
			I(1, 'Processor', '32')
			I(1, 'OS', 'NT 10.0')
			I(1, 'Product', 'HFSS Version 2024.2.0')
		$end 'StartInfo'
		$begin 'TotalInfo'
			I(1, 'Elapsed Time', '00:01:58')
			I(1, 'ComEngine Memory', '77.4 M')
		$end 'TotalInfo'
		GroupOptions=8
		TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
		ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 1, \'Executing From\', \'C:\\\\Program Files\\\\AnsysEM\\\\v242\\\\Win64\\\\HFSSCOMENGINE.exe\')', false, true)
		$begin 'ProfileGroup'
			MajorVer=2024
			MinorVer=2
			Name='HPC'
			$begin 'StartInfo'
				I(1, 'Type', 'Auto')
				I(1, 'MPI Vendor', 'Intel')
				I(1, 'MPI Version', '2021')
			$end 'StartInfo'
			$begin 'TotalInfo'
				I(0, ' ')
			$end 'TotalInfo'
			GroupOptions=0
			TaskDataOptions(Memory=8)
			ProfileItem('Machine', 0, 0, 0, 0, 0, 'I(5, 1, \'Name\', \'simpl-dz11-2\', 1, \'Memory\', \'384 GB\', 3, \'RAM Limit\', 90, \'%f%%\', 2, \'Cores\', 4, false, 1, \'Free Disk Space\', \'76.5 GB\')', false, true)
		$end 'ProfileGroup'
		ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 1, \'Allow off core\', \'True\')', false, true)
		ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 1, \'Solution Basis Order\', \'1\')', false, true)
		ProfileItem('Design Validation', 0, 0, 0, 0, 0, 'I(1, 0, \'Elapsed time : 00:00:00 , HFSS ComEngine Memory : 70.6 M\')', false, true)
		ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Perform full validations with standard port validations\')', false, true)
		ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
		$begin 'ProfileGroup'
			MajorVer=2024
			MinorVer=2
			Name='Initial Meshing'
			$begin 'StartInfo'
				I(1, 'Time', '02/28/2026 15:10:02')
			$end 'StartInfo'
			$begin 'TotalInfo'
				I(1, 'Elapsed Time', '00:00:07')
			$end 'TotalInfo'
			GroupOptions=4
			TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
			ProfileItem('Mesh', 4, 0, 5, 0, 60000, 'I(3, 2, \'Tetrahedra\', 22160, false, 1, \'Type\', \'TAU\', 2, \'Cores\', 4, false)', true, true)
			ProfileItem('Coarsen', 1, 0, 1, 0, 60000, 'I(1, 2, \'Tetrahedra\', 2801, false)', true, true)
			ProfileItem('Lambda Refine', 0, 0, 0, 0, 28212, 'I(2, 2, \'Tetrahedra\', 4166, false, 2, \'Cores\', 1, false)', true, true)
			ProfileItem('Simulation Setup', 0, 0, 0, 0, 180820, 'I(1, 1, \'Disk\', \'0 Bytes\')', true, true)
			ProfileItem('Port Adapt', 0, 0, 0, 0, 187712, 'I(2, 2, \'Tetrahedra\', 3368, false, 1, \'Disk\', \'2.87 KB\')', true, true)
			ProfileItem('Port Refine', 0, 0, 0, 0, 23124, 'I(2, 2, \'Tetrahedra\', 4197, false, 2, \'Cores\', 1, false)', true, true)
		$end 'ProfileGroup'
		$begin 'ProfileGroup'
			MajorVer=2024
			MinorVer=2
			Name='Adaptive Meshing'
			$begin 'StartInfo'
				I(1, 'Time', '02/28/2026 15:10:09')
			$end 'StartInfo'
			$begin 'TotalInfo'
				I(1, 'Elapsed Time', '00:01:02')
			$end 'TotalInfo'
			GroupOptions=4
			TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Adaptive Pass 1'
				$begin 'StartInfo'
					I(1, 'Frequency', '33GHz')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(0, ' ')
				$end 'TotalInfo'
				GroupOptions=0
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 183304, 'I(2, 2, \'Tetrahedra\', 3400, false, 1, \'Disk\', \'2.61 KB\')', true, true)
				ProfileItem('Matrix Assembly', 0, 0, 0, 0, 221116, 'I(3, 2, \'Tetrahedra\', 3400, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'33.1 KB\')', true, true)
				ProfileItem('Matrix Solve', 0, 0, 1, 0, 299604, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 23745, false, 3, \'Matrix bandwidth\', 20.4405, \'%5.1f\', 1, \'Disk\', \'95.8 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 0, 0, 299604, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'547 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 75232, 'I(1, 0, \'Adaptive Pass 1\')', true, true)
			$end 'ProfileGroup'
			ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Adaptive Pass 2'
				$begin 'StartInfo'
					I(1, 'Frequency', '33GHz')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(0, ' ')
				$end 'TotalInfo'
				GroupOptions=0
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 25872, 'I(2, 2, \'Tetrahedra\', 5219, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 185268, 'I(2, 2, \'Tetrahedra\', 4236, false, 1, \'Disk\', \'2.61 KB\')', true, true)
				ProfileItem('Matrix Assembly', 0, 0, 0, 0, 231532, 'I(3, 2, \'Tetrahedra\', 4236, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 0, 0, 2, 0, 334436, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 29387, false, 3, \'Matrix bandwidth\', 20.6165, \'%5.1f\', 1, \'Disk\', \'23.5 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 0, 0, 334436, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'289 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 75536, 'I(1, 0, \'Adaptive Pass 2\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 1.13248, \'%.5f\')', false, true)
			$end 'ProfileGroup'
			ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Adaptive Pass 3'
				$begin 'StartInfo'
					I(1, 'Frequency', '33GHz')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(0, ' ')
				$end 'TotalInfo'
				GroupOptions=0
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 27504, 'I(2, 2, \'Tetrahedra\', 6495, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 187680, 'I(2, 2, \'Tetrahedra\', 5278, false, 1, \'Disk\', \'2.61 KB\')', true, true)
				ProfileItem('Matrix Assembly', 0, 0, 1, 0, 244660, 'I(3, 2, \'Tetrahedra\', 5278, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 0, 0, 2, 0, 370836, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 36441, false, 3, \'Matrix bandwidth\', 20.7484, \'%5.1f\', 1, \'Disk\', \'29 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 0, 0, 370836, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'331 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76100, 'I(1, 0, \'Adaptive Pass 3\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.856645, \'%.5f\')', false, true)
			$end 'ProfileGroup'
			ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Adaptive Pass 4'
				$begin 'StartInfo'
					I(1, 'Frequency', '33GHz')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(0, ' ')
				$end 'TotalInfo'
				GroupOptions=0
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 29160, 'I(2, 2, \'Tetrahedra\', 8079, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 191900, 'I(2, 2, \'Tetrahedra\', 6618, false, 1, \'Disk\', \'2.61 KB\')', true, true)
				ProfileItem('Matrix Assembly', 0, 0, 1, 0, 260992, 'I(3, 2, \'Tetrahedra\', 6618, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 1, 0, 3, 0, 435580, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 45419, false, 3, \'Matrix bandwidth\', 20.8818, \'%5.1f\', 1, \'Disk\', \'36.5 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 0, 0, 435580, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'388 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76204, 'I(1, 0, \'Adaptive Pass 4\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.222373, \'%.5f\')', false, true)
			$end 'ProfileGroup'
			ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Adaptive Pass 5'
				$begin 'StartInfo'
					I(1, 'Frequency', '33GHz')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(0, ' ')
				$end 'TotalInfo'
				GroupOptions=0
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 31012, 'I(2, 2, \'Tetrahedra\', 10066, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 195964, 'I(2, 2, \'Tetrahedra\', 8319, false, 1, \'Disk\', \'2.61 KB\')', true, true)
				ProfileItem('Matrix Assembly', 0, 0, 1, 0, 281996, 'I(3, 2, \'Tetrahedra\', 8319, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 1, 0, 3, 0, 502792, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 56793, false, 3, \'Matrix bandwidth\', 21.0015, \'%5.1f\', 1, \'Disk\', \'45.8 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 0, 0, 502792, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'459 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76348, 'I(1, 0, \'Adaptive Pass 5\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.234137, \'%.5f\')', false, true)
			$end 'ProfileGroup'
			ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Adaptive Pass 6'
				$begin 'StartInfo'
					I(1, 'Frequency', '33GHz')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(0, ' ')
				$end 'TotalInfo'
				GroupOptions=0
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 33776, 'I(2, 2, \'Tetrahedra\', 12566, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 200992, 'I(2, 2, \'Tetrahedra\', 10548, false, 1, \'Disk\', \'2.61 KB\')', true, true)
				ProfileItem('Matrix Assembly', 0, 0, 1, 0, 307724, 'I(3, 2, \'Tetrahedra\', 10548, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 1, 0, 4, 0, 590440, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 71483, false, 3, \'Matrix bandwidth\', 21.1445, \'%5.1f\', 1, \'Disk\', \'58.8 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 0, 0, 590440, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'557 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76452, 'I(1, 0, \'Adaptive Pass 6\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.107919, \'%.5f\')', false, true)
			$end 'ProfileGroup'
			ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Adaptive Pass 7'
				$begin 'StartInfo'
					I(1, 'Frequency', '33GHz')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(0, ' ')
				$end 'TotalInfo'
				GroupOptions=0
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 35688, 'I(2, 2, \'Tetrahedra\', 15044, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 205632, 'I(2, 2, \'Tetrahedra\', 12753, false, 1, \'Disk\', \'6.48 KB\')', true, true)
				ProfileItem('Matrix Assembly', 1, 0, 2, 0, 334352, 'I(3, 2, \'Tetrahedra\', 12753, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'75 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 2, 0, 5, 0, 680788, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 85999, false, 3, \'Matrix bandwidth\', 21.2385, \'%5.1f\', 1, \'Disk\', \'58.1 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 0, 0, 680788, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'596 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76556, 'I(1, 0, \'Adaptive Pass 7\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.0552177, \'%.5f\')', false, true)
			$end 'ProfileGroup'
			ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Adaptive Pass 8'
				$begin 'StartInfo'
					I(1, 'Frequency', '33GHz')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(0, ' ')
				$end 'TotalInfo'
				GroupOptions=0
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 40200, 'I(2, 2, \'Tetrahedra\', 18440, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 213136, 'I(2, 2, \'Tetrahedra\', 15744, false, 1, \'Disk\', \'6.48 KB\')', true, true)
				ProfileItem('Matrix Assembly', 1, 0, 2, 0, 370556, 'I(3, 2, \'Tetrahedra\', 15744, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 2, 0, 7, 0, 817168, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 105795, false, 3, \'Matrix bandwidth\', 21.3151, \'%5.1f\', 1, \'Disk\', \'78.7 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 1, 0, 817168, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'737 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76616, 'I(1, 0, \'Adaptive Pass 8\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.0463512, \'%.5f\')', false, true)
			$end 'ProfileGroup'
			ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Adaptive Pass 9'
				$begin 'StartInfo'
					I(1, 'Frequency', '33GHz')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(0, ' ')
				$end 'TotalInfo'
				GroupOptions=0
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 40912, 'I(2, 2, \'Tetrahedra\', 21168, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 220552, 'I(2, 2, \'Tetrahedra\', 18176, false, 1, \'Disk\', \'6.48 KB\')', true, true)
				ProfileItem('Matrix Assembly', 1, 0, 3, 0, 400604, 'I(3, 2, \'Tetrahedra\', 18176, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'75 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 3, 0, 8, 0, 918036, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 121825, false, 3, \'Matrix bandwidth\', 21.3642, \'%5.1f\', 1, \'Disk\', \'64 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 1, 0, 918036, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'723 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76588, 'I(1, 0, \'Adaptive Pass 9\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.0256816, \'%.5f\')', false, true)
			$end 'ProfileGroup'
			ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Adaptive Pass 10'
				$begin 'StartInfo'
					I(1, 'Frequency', '33GHz')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(0, ' ')
				$end 'TotalInfo'
				GroupOptions=0
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 42480, 'I(2, 2, \'Tetrahedra\', 23626, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 224996, 'I(2, 2, \'Tetrahedra\', 20379, false, 1, \'Disk\', \'10.2 KB\')', true, true)
				ProfileItem('Matrix Assembly', 1, 0, 3, 0, 427040, 'I(3, 2, \'Tetrahedra\', 20379, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 3, 0, 10, 0, 1037824, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 136313, false, 3, \'Matrix bandwidth\', 21.4043, \'%5.1f\', 1, \'Disk\', \'58 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 1, 0, 1037824, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'740 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76596, 'I(1, 0, \'Adaptive Pass 10\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.0149611, \'%.5f\')', false, true)
			$end 'ProfileGroup'
			ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Adaptive Pass 11'
				$begin 'StartInfo'
					I(1, 'Frequency', '33GHz')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(0, ' ')
				$end 'TotalInfo'
				GroupOptions=0
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem('Adaptive Refine', 0, 0, 0, 0, 42500, 'I(2, 2, \'Tetrahedra\', 25313, false, 2, \'Cores\', 1, false)', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('Simulation Setup ', 0, 0, 0, 0, 228480, 'I(2, 2, \'Tetrahedra\', 21922, false, 1, \'Disk\', \'10.2 KB\')', true, true)
				ProfileItem('Matrix Assembly', 1, 0, 3, 0, 443792, 'I(3, 2, \'Tetrahedra\', 21922, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, true)
				ProfileItem('Matrix Solve', 3, 0, 10, 0, 1082784, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 4, false, 2, \'Matrix size\', 146435, false, 3, \'Matrix bandwidth\', 21.4302, \'%5.1f\', 1, \'Disk\', \'41 KB\')', true, true)
				ProfileItem('Field Recovery', 0, 0, 1, 0, 1082784, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'698 KB\')', true, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 76696, 'I(1, 0, \'Adaptive Pass 11\')', true, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 3, \'Max Mag. Delta S\', 0.00788595, \'%.5f\')', false, true)
			$end 'ProfileGroup'
			ProfileFootnote('I(1, 0, \'Adaptive Passes converged\')', 0)
		$end 'ProfileGroup'
		$begin 'ProfileGroup'
			MajorVer=2024
			MinorVer=2
			Name='Frequency Sweep'
			$begin 'StartInfo'
				I(1, 'Time', '02/28/2026 15:11:12')
			$end 'StartInfo'
			$begin 'TotalInfo'
				I(1, 'Elapsed Time', '00:00:48')
			$end 'TotalInfo'
			GroupOptions=4
			TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
			ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 1, \'HPC\', \'Enabled\')', false, true)
			$begin 'ProfileGroup'
				MajorVer=2024
				MinorVer=2
				Name='Solution - Sweep'
				$begin 'StartInfo'
					I(0, 'Interpolating HFSS Frequency Sweep, Solving Distributed - up to 4 frequencies in parallel')
					I(1, 'Time', '02/28/2026 15:11:12')
				$end 'StartInfo'
				$begin 'TotalInfo'
					I(1, 'Elapsed Time', '00:00:48')
				$end 'TotalInfo'
				GroupOptions=4
				TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'From 23GHz to 33GHz, 201 Frequencies\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Frequency: 33GHz has already been solved\')', false, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 23GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:10')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #1\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 252772, 'I(2, 2, \'Tetrahedra\', 21922, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 322920, 'I(3, 2, \'Tetrahedra\', 21922, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 7, 0, 7, 0, 1137744, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 146435, false, 3, \'Matrix bandwidth\', 21.4302, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1137744, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'158 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 28GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:10')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #1\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 253392, 'I(2, 2, \'Tetrahedra\', 21922, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 324096, 'I(3, 2, \'Tetrahedra\', 21922, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 6, 0, 6, 0, 1139408, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 146435, false, 3, \'Matrix bandwidth\', 21.4302, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1139408, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'158 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 25.5GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:10')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #1\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 252008, 'I(2, 2, \'Tetrahedra\', 21922, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 322412, 'I(3, 2, \'Tetrahedra\', 21922, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 7, 0, 7, 0, 1137960, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 146435, false, 3, \'Matrix bandwidth\', 21.4302, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1137960, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'158 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 30.5GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:10')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #1\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 251912, 'I(2, 2, \'Tetrahedra\', 21922, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 322140, 'I(3, 2, \'Tetrahedra\', 21922, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 6, 0, 6, 0, 1138248, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 146435, false, 3, \'Matrix bandwidth\', 21.4302, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1138248, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'158 KB\')', true, false)
				$end 'ProfileGroup'
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 1, Frequency: 33GHz; Additional basis points are needed before the interpolation error can be computed.\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 2, Frequency: 23GHz; Additional basis points are needed before the interpolation error can be computed.\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 3, Frequency: 28GHz; S Matrix Error = 107.240%\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 4, Frequency: 25.5GHz; S Matrix Error =  83.102%\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 5, Frequency: 30.5GHz; S Matrix Error =  42.646%\')', false, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 31.75GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:10')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #2\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 254084, 'I(2, 2, \'Tetrahedra\', 21922, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 324936, 'I(3, 2, \'Tetrahedra\', 21922, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 6, 0, 6, 0, 1140624, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 146435, false, 3, \'Matrix bandwidth\', 21.4302, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1140624, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'158 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 29.25GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:11')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #2\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 254204, 'I(2, 2, \'Tetrahedra\', 21922, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 325136, 'I(3, 2, \'Tetrahedra\', 21922, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 6, 0, 6, 0, 1140304, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 146435, false, 3, \'Matrix bandwidth\', 21.4302, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1140304, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'158 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 26.75GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:10')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #2\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 252456, 'I(2, 2, \'Tetrahedra\', 21922, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 322852, 'I(3, 2, \'Tetrahedra\', 21922, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 6, 0, 6, 0, 1139096, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 146435, false, 3, \'Matrix bandwidth\', 21.4302, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1139096, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'158 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 24.25GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:10')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #2\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 251852, 'I(2, 2, \'Tetrahedra\', 21922, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 322632, 'I(3, 2, \'Tetrahedra\', 21922, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 6, 0, 6, 0, 1137624, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 146435, false, 3, \'Matrix bandwidth\', 21.4302, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1137624, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'158 KB\')', true, false)
				$end 'ProfileGroup'
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 6, Frequency: 31.75GHz; S Matrix Error =  20.423%\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 7, Frequency: 29.25GHz; S Matrix Error =  20.065%\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 8, Frequency: 26.75GHz; S Matrix Error =   4.063%\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 9, Frequency: 24.25GHz; S Matrix Error =   1.264%\')', false, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 78784, 'I(1, 0, \'Frequency Group #2; Interpolating frequency sweep\')', true, true)
				ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 32.375GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:10')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #3\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 253076, 'I(2, 2, \'Tetrahedra\', 21922, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 323556, 'I(3, 2, \'Tetrahedra\', 21922, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 6, 0, 6, 0, 1138804, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 146435, false, 3, \'Matrix bandwidth\', 21.4302, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1138804, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'158 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 31.125GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:11')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #3\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 253036, 'I(2, 2, \'Tetrahedra\', 21922, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 323264, 'I(3, 2, \'Tetrahedra\', 21922, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 6, 0, 6, 0, 1139696, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 146435, false, 3, \'Matrix bandwidth\', 21.4302, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1139696, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'158 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 29.875GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:10')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #3\')', false, true)
					ProfileItem(' ', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 252336, 'I(2, 2, \'Tetrahedra\', 21922, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 323212, 'I(3, 2, \'Tetrahedra\', 21922, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 6, 0, 6, 0, 1138288, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 146435, false, 3, \'Matrix bandwidth\', 21.4302, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1138288, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'158 KB\')', true, false)
				$end 'ProfileGroup'
				$begin 'ProfileGroup'
					MajorVer=2024
					MinorVer=2
					Name='Frequency - 28.625GHz'
					$begin 'StartInfo'
						I(0, 'simpl-dz11-2')
					$end 'StartInfo'
					$begin 'TotalInfo'
						I(0, 'Elapsed time : 00:00:10')
					$end 'TotalInfo'
					GroupOptions=0
					TaskDataOptions('CPU Time'=8, 'Real Time'=8)
					ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Distributed Solve Group #3\')', false, true)
					ProfileItem('Simulation Setup ', 0, 0, 0, 0, 251900, 'I(2, 2, \'Tetrahedra\', 21922, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Assembly', 2, 0, 2, 0, 322456, 'I(3, 2, \'Tetrahedra\', 21922, false, 2, \'Lumped ports\', 1, false, 1, \'Disk\', \'0 Bytes\')', true, false)
					ProfileItem('Matrix Solve', 6, 0, 6, 0, 1138052, 'I(5, 1, \'Type\', \'DCS\', 2, \'Cores\', 1, false, 2, \'Matrix size\', 146435, false, 3, \'Matrix bandwidth\', 21.4302, \'%5.1f\', 1, \'Disk\', \'1.42 KB\')', true, false)
					ProfileItem('Field Recovery', 0, 0, 0, 0, 1138052, 'I(2, 2, \'Excitations\', 1, false, 1, \'Disk\', \'158 KB\')', true, false)
				$end 'ProfileGroup'
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 10, Frequency: 32.375GHz; S Matrix Error =   0.307%; Secondary solver criterion is not converged\')', false, true)
				ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'Basis Element # 11, Frequency: 31.125GHz; Scattering matrix quantities converged; Passive within tolerance\')', false, true)
				ProfileItem('Data Transfer', 0, 0, 0, 0, 78904, 'I(1, 0, \'Frequency Group #3; Interpolating frequency sweep\')', true, true)
				ProfileFootnote('I(1, 0, \'Interpolating sweep converged and is passive\')', 0)
				ProfileFootnote('I(1, 0, \'HFSS: Distributed Interpolating sweep\')', 0)
			$end 'ProfileGroup'
		$end 'ProfileGroup'
		ProfileItem('', 0, 0, 0, 0, 0, 'I(1, 0, \'\')', false, true)
		$begin 'ProfileGroup'
			MajorVer=2024
			MinorVer=2
			Name='Simulation Summary'
			$begin 'StartInfo'
			$end 'StartInfo'
			$begin 'TotalInfo'
				I(0, ' ')
			$end 'TotalInfo'
			GroupOptions=0
			TaskDataOptions('CPU Time'=8, Memory=8, 'Real Time'=8)
			ProfileItem('Design Validation', 0, 0, 0, 0, 0, 'I(2, 1, \'Elapsed Time\', \'00:00:00\', 1, \'Total Memory\', \'70.6 MB\')', false, true)
			ProfileItem('Initial Meshing', 0, 0, 0, 0, 0, 'I(2, 1, \'Elapsed Time\', \'00:00:07\', 1, \'Total Memory\', \'242 MB\')', false, true)
			ProfileItem('Adaptive Meshing', 0, 0, 0, 0, 0, 'I(5, 1, \'Elapsed Time\', \'00:01:02\', 1, \'Average memory/process\', \'1.03 GB\', 1, \'Max memory/process\', \'1.03 GB\', 2, \'Max number of processes/frequency\', 1, false, 2, \'Total number of cores\', 4, false)', false, true)
			ProfileItem('Frequency Sweep', 0, 0, 0, 0, 0, 'I(5, 1, \'Elapsed Time\', \'00:00:48\', 1, \'Average memory/process\', \'1.09 GB\', 1, \'Max memory/process\', \'1.09 GB\', 2, \'Max number of processes/frequency\', 1, false, 2, \'Total number of cores\', 4, false)', false, true)
			ProfileFootnote('I(3, 2, \'Max solved tets\', 21922, false, 2, \'Max matrix size\', 146435, false, 1, \'Matrix bandwidth\', \'21.4\')', 0)
		$end 'ProfileGroup'
		ProfileFootnote('I(2, 1, \'Stop Time\', \'02/28/2026 15:12:00\', 1, \'Status\', \'Normal Completion\')', 0)
	$end 'ProfileGroup'
$end 'Profile'
